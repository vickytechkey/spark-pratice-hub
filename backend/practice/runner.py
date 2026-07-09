import time
import json
import traceback
import uuid
import sys
import datetime
from django.utils import timezone
from pyspark.sql import SparkSession
from practice.models import Problem, TestCase, Dataset, Submission, SparkProfile, DailyActivity

def get_spark_session(profile_name):
    """
    Creates or retrieves a SparkSession configured with the specified profile.
    """
    profile = SparkProfile.objects.filter(name=profile_name).first()
    if not profile:
        profile_dict = {
            "master": "local[*]",
            "driver_memory": "1g",
            "executor_memory": "1g",
            "executor_cores": 1,
            "shuffle_partitions": 2,
            "adaptive_query_execution": True,
            "broadcast_threshold": 10485760,
            "serializer": "org.apache.spark.serializer.KryoSerializer",
            "default_parallelism": 2,
            "extra_configs": None
        }
    else:
        profile_dict = {
            "master": profile.master,
            "driver_memory": profile.driver_memory,
            "executor_memory": profile.executor_memory,
            "executor_cores": profile.executor_cores,
            "shuffle_partitions": profile.shuffle_partitions,
            "adaptive_query_execution": profile.adaptive_query_execution,
            "broadcast_threshold": profile.broadcast_threshold,
            "serializer": profile.serializer,
            "default_parallelism": profile.default_parallelism,
            "extra_configs": profile.extra_configs
        }
        
    builder = SparkSession.builder.appName(f"SparkPracticeHub-{profile_name}")
    builder = builder.master(profile_dict["master"])
    builder = builder.config("spark.driver.memory", profile_dict["driver_memory"])
    builder = builder.config("spark.executor.memory", profile_dict["executor_memory"])
    builder = builder.config("spark.executor.cores", str(profile_dict["executor_cores"]))
    builder = builder.config("spark.sql.shuffle.partitions", str(profile_dict["shuffle_partitions"]))
    builder = builder.config("spark.sql.adaptive.enabled", "true" if profile_dict["adaptive_query_execution"] else "false")
    builder = builder.config("spark.sql.autoBroadcastJoinThreshold", str(profile_dict["broadcast_threshold"]))
    builder = builder.config("spark.serializer", profile_dict["serializer"])
    builder = builder.config("spark.default.parallelism", str(profile_dict["default_parallelism"]))
    
    if profile_dict.get("extra_configs"):
        try:
            extra = profile_dict["extra_configs"]
            if isinstance(extra, str):
                extra = json.loads(extra)
            for k, v in extra.items():
                builder = builder.config(k, str(v))
        except Exception:
            pass
            
    # Stop existing Spark session if running to apply new configurations
    try:
        active_session = SparkSession.getActiveSession()
        if active_session:
            active_session.stop()
    except Exception:
        pass
        
    spark = builder.getOrCreate()
    return spark

def compare_dataframes(actual_df, expected_df, mode="Exact"):
    """
    Compares two Spark DataFrames based on the specified mode.
    """
    if mode == "Row count":
        return actual_df.count() == expected_df.count(), f"Actual count: {actual_df.count()}, Expected: {expected_df.count()}"
        
    actual_schema = [(field.name, field.dataType.simpleString()) for field in actual_df.schema]
    expected_schema = [(field.name, field.dataType.simpleString()) for field in expected_df.schema]
    
    if actual_schema != expected_schema:
        return False, f"Schema mismatch.\nActual: {actual_schema}\nExpected: {expected_schema}"
        
    if mode == "Schema only":
        return True, "Schema matches."
        
    if mode == "Ignore row order":
        if actual_df.count() != expected_df.count():
            return False, f"Row count mismatch. Actual: {actual_df.count()}, Expected: {expected_df.count()}"
        diff1 = actual_df.subtract(expected_df).count()
        diff2 = expected_df.subtract(actual_df).count()
        if diff1 == 0 and diff2 == 0:
            return True, "All rows match (ignoring order)."
        else:
            return False, f"Data mismatch. Rows in actual not in expected: {diff1}. Rows in expected not in actual: {diff2}."
            
    # Default is "Exact"
    cols = actual_df.columns
    actual_sorted = actual_df.sort(*cols).collect()
    expected_sorted = expected_df.sort(*cols).collect()
    
    if len(actual_sorted) != len(expected_sorted):
        return False, f"Row count mismatch. Actual: {len(actual_sorted)}, Expected: {len(expected_sorted)}"
        
    for i, (act, exp) in enumerate(zip(actual_sorted, expected_sorted)):
        if act != exp:
            return False, f"Mismatch at sorted row {i+1}.\nActual: {act}\nExpected: {exp}"
            
    return True, "Exact match verified."

def run_solution(problem_id, user_code_str, profile_name="Interview", submit=True):
    """
    Loads test cases for the problem, launches Spark with the profile, 
    executes user solution, and validates outputs.
    """
    problem = Problem.objects.filter(id=problem_id).first()
    if not problem:
        return {"status": "ERROR", "message": "Problem not found."}
        
    test_cases = TestCase.objects.filter(problem=problem)
    if not test_cases.exists():
        return {"status": "ERROR", "message": "No test cases found for this problem."}
        
    spark = None
    try:
        spark = get_spark_session(profile_name)
    except Exception as e:
        return {"status": "ERROR", "message": f"Failed to start Spark Session: {str(e)}", "traceback": traceback.format_exc()}
        
    results = []
    all_passed = True
    total_time_ms = 0
    spark_metrics = {
        "jobs": 0,
        "stages": 0,
        "tasks": 0,
        "shuffle_read_bytes": 0,
        "shuffle_write_bytes": 0
    }
    
    # Compile user function
    namespace = {}
    try:
        exec(user_code_str, namespace)
        if "solve" not in namespace or not callable(namespace["solve"]):
            return {"status": "ERROR", "message": "Your code must define a function named 'solve(spark, inputs)'"}
        solve_func = namespace["solve"]
    except Exception as e:
        return {"status": "ERROR", "message": f"Compilation Error: {str(e)}", "traceback": traceback.format_exc()}
        
    # Execute Test Cases
    if not submit:
        test_cases = list(test_cases)[:3]

    for tc_idx, tc in enumerate(test_cases):
        job_group_id = str(uuid.uuid4())
        spark.sparkContext.setJobGroup(job_group_id, f"Test Case {tc_idx+1}")
        
        # Load input DataFrames
        inputs = {}
        try:
            for input_name, dataset_name in tc.input_datasets.items():
                dataset = Dataset.objects.filter(name=dataset_name).first()
                if not dataset:
                    raise ValueError(f"Dataset '{dataset_name}' not registered.")
                
                ftype = dataset.type.upper()
                fpath = dataset.file_path
                if ftype == "CSV":
                    inputs[input_name] = spark.read.option("header", "true").option("inferSchema", "true").csv(fpath)
                elif ftype == "PARQUET":
                    inputs[input_name] = spark.read.parquet(fpath)
                elif ftype == "JSON":
                    inputs[input_name] = spark.read.option("multiline", "true").json(fpath)
                elif ftype == "EXCEL":
                    import pandas as pd
                    df_pd = pd.read_excel(fpath)
                    inputs[input_name] = spark.createDataFrame(df_pd)
        except Exception as e:
            all_passed = False
            results.append({
                "test_case_id": tc.id,
                "passed": False,
                "message": f"Error loading inputs: {str(e)}"
            })
            continue
            
        # Load Expected Output DataFrame
        expected_dataset = Dataset.objects.filter(name=tc.expected_output_dataset).first()
        if not expected_dataset:
            all_passed = False
            results.append({
                "test_case_id": tc.id,
                "passed": False,
                "message": f"Expected dataset '{tc.expected_output_dataset}' not found."
            })
            continue
            
        try:
            ftype = expected_dataset.type.upper()
            fpath = expected_dataset.file_path
            if ftype == "CSV":
                expected_df = spark.read.option("header", "true").option("inferSchema", "true").csv(fpath)
            elif ftype == "PARQUET":
                expected_df = spark.read.parquet(fpath)
            elif ftype == "JSON":
                expected_df = spark.read.option("multiline", "true").json(fpath)
            elif ftype == "EXCEL":
                import pandas as pd
                df_pd = pd.read_excel(fpath)
                expected_df = spark.createDataFrame(df_pd)
        except Exception as e:
            all_passed = False
            results.append({
                "test_case_id": tc.id,
                "passed": False,
                "message": f"Error loading expected output: {str(e)}"
            })
            continue
            
        # Run User's Solution
        t_start = time.perf_counter()
        try:
            actual_df = solve_func(spark, inputs)
            if actual_df is None:
                raise ValueError("The 'solve' function returned None. It must return a Spark DataFrame.")
                
            actual_df.cache()
            actual_count = actual_df.count() 
            
            # Compare output
            comp_mode = tc.comparison_mode or problem.comparison_mode or "Exact"
            passed, comp_msg = compare_dataframes(actual_df, expected_df, mode=comp_mode)
            
            t_end = time.perf_counter()
            duration_ms = int((t_end - t_start) * 1000)
            total_time_ms += duration_ms
            
            # Retrieve metrics from statusTracker
            tracker = spark.sparkContext.statusTracker()
            job_ids = tracker.getJobIdsForGroup(job_group_id)
            tc_jobs = len(job_ids)
            tc_stages = 0
            tc_tasks = 0
            
            for j_id in job_ids:
                j_info = tracker.getJobInfo(j_id)
                if j_info:
                    tc_stages += len(j_info.stageIds)
                    for s_id in j_info.stageIds:
                        s_info = tracker.getStageInfo(s_id)
                        if s_info:
                            tc_tasks += s_info.numCompletedTasks
                            
            spark_metrics["jobs"] += tc_jobs
            spark_metrics["stages"] += tc_stages
            spark_metrics["tasks"] += tc_tasks
            
            # Convert preview to dicts safely
            actual_preview = []
            expected_preview = []
            try:
                actual_preview = actual_df.limit(10).toPandas().to_dict(orient="records")
                expected_preview = expected_df.limit(10).toPandas().to_dict(orient="records")
            except Exception:
                pass

            results.append({
                "test_case_id": tc.id,
                "passed": passed,
                "message": comp_msg,
                "duration_ms": duration_ms,
                "actual_preview": actual_preview,
                "expected_preview": expected_preview,
                "actual_schema": [(f.name, f.dataType.simpleString()) for f in actual_df.schema],
                "expected_schema": [(f.name, f.dataType.simpleString()) for f in expected_df.schema]
            })
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            all_passed = False
            results.append({
                "test_case_id": tc.id,
                "passed": False,
                "message": f"Execution Error: {str(e)}",
                "traceback": traceback.format_exc()
            })
            
    status = "PASS" if all_passed else "FAIL"
    if submit:
        # Create Submission record
        Submission.objects.create(
            problem=problem,
            code=user_code_str,
            status=status,
            execution_time_ms=total_time_ms,
            metrics=spark_metrics,
            error_message=None if all_passed else "\n".join([r.get("message", "") for r in results if not r["passed"]])
        )
        
        # Update daily activity
        today_date = datetime.date.today()
        activity, created = DailyActivity.objects.get_or_create(
            date=today_date,
            defaults={'attempts': 0, 'solved': 0}
        )
        activity.attempts += 1
        if status == "PASS":
            # Check if this problem was solved already by this user previously
            already_solved = Submission.objects.filter(problem=problem, status="PASS").exclude(timestamp__date=today_date).exists()
            if not already_solved:
                activity.solved += 1
        activity.save()
    
    return {
        "status": status,
        "results": results,
        "total_time_ms": total_time_ms,
        "metrics": spark_metrics
    }
