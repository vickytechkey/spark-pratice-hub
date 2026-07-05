import time
import json
import traceback
import uuid
import sys
from pyspark.sql import SparkSession
from database import db

def get_spark_session(profile_name):
    """
    Creates or retrieves a SparkSession configured with the specified profile.
    """
    profile = db.get_profile(profile_name)
    if not profile:
        profile = {
            "master": "local[*]",
            "driver_memory": "1g",
            "executor_memory": "1g",
            "executor_cores": 1,
            "shuffle_partitions": 2,
            "adaptive_query_execution": 1,
            "broadcast_threshold": 10485760,
            "serializer": "org.apache.spark.serializer.KryoSerializer",
            "default_parallelism": 2,
            "extra_configs": None
        }
        
    builder = SparkSession.builder.appName(f"SparkPracticeHub-{profile_name}")
    builder = builder.master(profile["master"])
    builder = builder.config("spark.driver.memory", profile["driver_memory"])
    builder = builder.config("spark.executor.memory", profile["executor_memory"])
    builder = builder.config("spark.executor.cores", str(profile["executor_cores"]))
    builder = builder.config("spark.sql.shuffle.partitions", str(profile["shuffle_partitions"]))
    builder = builder.config("spark.sql.adaptive.enabled", "true" if profile["adaptive_query_execution"] == 1 else "false")
    builder = builder.config("spark.sql.autoBroadcastJoinThreshold", str(profile["broadcast_threshold"]))
    builder = builder.config("spark.serializer", profile["serializer"])
    builder = builder.config("spark.default.parallelism", str(profile["default_parallelism"]))
    
    if profile.get("extra_configs"):
        try:
            extra = json.loads(profile["extra_configs"])
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
    # 1. Row count comparison mode
    if mode == "Row count":
        return actual_df.count() == expected_df.count(), f"Actual count: {actual_df.count()}, Expected: {expected_df.count()}"
        
    # 2. Schema only comparison mode
    actual_schema = [(field.name, field.dataType.simpleString()) for field in actual_df.schema]
    expected_schema = [(field.name, field.dataType.simpleString()) for field in expected_df.schema]
    
    if actual_schema != expected_schema:
        return False, f"Schema mismatch.\nActual: {actual_schema}\nExpected: {expected_schema}"
        
    if mode == "Schema only":
        return True, "Schema matches."
        
    # 3. Content comparison modes
    if mode == "Ignore row order":
        # Check counts first
        if actual_df.count() != expected_df.count():
            return False, f"Row count mismatch. Actual: {actual_df.count()}, Expected: {expected_df.count()}"
        # Subtract check
        diff1 = actual_df.subtract(expected_df).count()
        diff2 = expected_df.subtract(actual_df).count()
        if diff1 == 0 and diff2 == 0:
            return True, "All rows match (ignoring order)."
        else:
            return False, f"Data mismatch. Rows in actual not in expected: {diff1}. Rows in expected not in actual: {diff2}."
            
    # Default is "Exact" (compares content exactly, including row ordering if specified, or by sorting)
    # Let's sort by all columns to make a stable comparison since Spark row order is non-deterministic unless sorted
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
    problem = db.get_problem(problem_id)
    if not problem:
        return {"status": "ERROR", "message": "Problem not found."}
        
    test_cases = db.get_test_cases(problem_id)
    if not test_cases:
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
    # The user should define: def solve(spark, inputs):
    namespace = {}
    try:
        exec(user_code_str, namespace)
        if "solve" not in namespace or not callable(namespace["solve"]):
            return {"status": "ERROR", "message": "Your code must define a function named 'solve(spark, inputs)'"}
        solve_func = namespace["solve"]
    except Exception as e:
        return {"status": "ERROR", "message": f"Compilation Error: {str(e)}", "traceback": traceback.format_exc()}
        
    # Execute Test Cases
    for tc_idx, tc in enumerate(test_cases):
        # Setup Job Group for metrics tracking
        job_group_id = str(uuid.uuid4())
        spark.sparkContext.setJobGroup(job_group_id, f"Test Case {tc_idx+1}")
        
        # Load input DataFrames
        inputs = {}
        try:
            for input_name, dataset_name in tc["input_datasets"].items():
                dataset = db.get_dataset(dataset_name)
                if not dataset:
                    raise ValueError(f"Dataset '{dataset_name}' not registered.")
                
                # Load based on type
                ftype = dataset["type"]
                fpath = dataset["file_path"]
                if ftype == "CSV":
                    inputs[input_name] = spark.read.option("header", "true").option("inferSchema", "true").csv(fpath)
                elif ftype == "PARQUET":
                    inputs[input_name] = spark.read.parquet(fpath)
                elif ftype == "JSON":
                    inputs[input_name] = spark.read.option("multiline", "true").json(fpath)
                elif ftype == "EXCEL":
                    # Spark doesn't read Excel natively easily without extra jars.
                    # Since we imported Excel data into pandas and wrote it as CSV/JSON,
                    # the database type is converted or we load it using pandas first, then create DataFrame.
                    import pandas as pd
                    df_pd = pd.read_excel(fpath)
                    inputs[input_name] = spark.createDataFrame(df_pd)
        except Exception as e:
            all_passed = False
            results.append({
                "test_case_id": tc["id"],
                "passed": False,
                "message": f"Error loading inputs: {str(e)}"
            })
            continue
            
        # Load Expected Output DataFrame
        expected_dataset = db.get_dataset(tc["expected_output_dataset"])
        if not expected_dataset:
            all_passed = False
            results.append({
                "test_case_id": tc["id"],
                "passed": False,
                "message": f"Expected dataset '{tc['expected_output_dataset']}' not found."
            })
            continue
            
        try:
            ftype = expected_dataset["type"]
            fpath = expected_dataset["file_path"]
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
                "test_case_id": tc["id"],
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
                
            # Perform action to trigger Spark execution and get performance metrics
            # E.g., caching or just forcing evaluation
            actual_df.cache()
            actual_count = actual_df.count() 
            
            # Compare output
            comp_mode = tc.get("comparison_mode") or problem.get("comparison_mode") or "Exact"
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
            
            results.append({
                "test_case_id": tc["id"],
                "passed": passed,
                "message": comp_msg,
                "duration_ms": duration_ms,
                "actual_preview": actual_df.limit(10).toPandas().to_dict(orient="records"),
                "expected_preview": expected_df.limit(10).toPandas().to_dict(orient="records"),
                "actual_schema": [(f.name, f.dataType.simpleString()) for f in actual_df.schema],
                "expected_schema": [(f.name, f.dataType.simpleString()) for f in expected_df.schema]
            })
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            all_passed = False
            results.append({
                "test_case_id": tc["id"],
                "passed": False,
                "message": f"Execution Error: {str(e)}",
                "traceback": traceback.format_exc()
            })
            
    # Save submission in database
    status = "PASS" if all_passed else "FAIL"
    if submit:
        db.add_submission(
            problem_id=problem_id,
            code=user_code_str,
            status=status,
            execution_time_ms=total_time_ms,
            metrics=spark_metrics,
            error_message=None if all_passed else "\n".join([r.get("message", "") for r in results if not r["passed"]])
        )
    
    return {
        "status": status,
        "results": results,
        "total_time_ms": total_time_ms,
        "metrics": spark_metrics
    }
