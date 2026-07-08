import os
import json
import sqlite3
import random

random.seed(42)

DB_PATH = "database/spark_practice.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        difficulty TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        concepts TEXT,
        hints TEXT,
        comparison_mode TEXT DEFAULT 'Exact'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        input_datasets TEXT NOT NULL,
        expected_output_dataset TEXT NOT NULL,
        comparison_mode TEXT,
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        name TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        file_path TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def save_dataset(name, data):
    os.makedirs("datasets", exist_ok=True)
    file_path = f"datasets/{name}.json"
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO datasets (name, type, file_path) VALUES (?, ?, ?)", (name, "JSON", file_path))
    conn.commit()
    conn.close()

def clear_old_data(problem_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM test_cases WHERE problem_id = ?", (problem_id,))
    cursor.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
    conn.commit()
    conn.close()

def save_problem(prob):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO problems (id, title, difficulty, category, description, concepts, hints, comparison_mode)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (prob['id'], prob['title'], prob['difficulty'], prob['category'], prob['description'], prob['concepts'], prob['hints'], prob['comparison_mode']))
    conn.commit()
    conn.close()

def save_testcase(problem_id, input_data_dict, expected_data, tc_idx, comparison_mode):
    # Save input datasets
    input_mappings = {}
    for key, data in input_data_dict.items():
        ds_name = f"{problem_id}_{key}_tc{tc_idx}"
        save_dataset(ds_name, data)
        input_mappings[key] = ds_name
        
    exp_ds_name = f"{problem_id}_expected_tc{tc_idx}"
    save_dataset(exp_ds_name, expected_data)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO test_cases (problem_id, input_datasets, expected_output_dataset, comparison_mode)
    VALUES (?, ?, ?, ?)
    """, (problem_id, json.dumps(input_mappings), exp_ds_name, comparison_mode))
    conn.commit()
    conn.close()

categories = [
    "Filtering & Sorting",
    "Date & String",
    "Aggregations",
    "Joins",
    "Advanced Nested & Pivot",
    "Window Functions",
    "Data Cleaning & Null Handling",
    "Performance & Optimization",
    "Array & Map Operations",
    "User Defined Functions (UDFs)"
]

def generate_all():
    init_db()
    
    for cat in categories:
        print(f"Generating for category: {cat}...")
        for i in range(1, 101):
            prob_id = f"SPK-{cat[:3].upper()}-{i:03d}".replace(" & ", "").replace(" ", "")
            difficulty = "Easy" if i <= 35 else "Medium" if i <= 80 else "Hard"
            
            # Setup problem basics
            title = ""
            desc = ""
            concepts = ""
            hints = ""
            comparison_mode = "Ignore row order"
            
            if cat == "Filtering & Sorting":
                val = i * 100
                title = f"Filter High Value Transactions V{i}"
                desc = f"Given a transaction DataFrame `df1`, filter transactions where the `amount` is strictly greater than {val}. Sort the results by `transaction_id` ascending."
                concepts = "filter, where, orderBy"
                hints = f"Use `df1.filter(df1.amount > {val})` and chain it with `.orderBy('transaction_id')`."
                comparison_mode = "Exact"
            elif cat == "Date & String":
                title = f"Clean Domain Names V{i}"
                desc = f"Given user accounts DataFrame `df1`, extract the user name (part before '@') from the `email` column, name the new column `username`, and keep only columns `user_id` and `username`. Append suffix '_{i}_tc' to username."
                concepts = "withColumn, split, select"
                hints = f"Use `split(df1.email, '@')[0]` to extract the name, and concat the suffix."
            elif cat == "Aggregations":
                title = f"Sum Active Points V{i}"
                desc = f"Group the user points DataFrame `df1` by `category`, sum the `points` column naming the result `total_points`, and filter to keep categories where `total_points` is greater than the dynamically set threshold."
                concepts = "groupBy, agg, sum, filter"
                hints = "Use `.groupBy('category').agg(sum('points').alias('total_points')).filter('total_points > threshold')`."
            elif cat == "Joins":
                title = f"Sales with Category V{i}"
                desc = "Perform an inner join between sales DataFrame `df1` and products DataFrame `df2` on `product_id`. Return all columns from both DataFrames (ensure you do not duplicate the key column)."
                concepts = "join, inner"
                hints = "Use `df1.join(df2, 'product_id')` to avoid duplicated columns."
            elif cat == "Advanced Nested & Pivot":
                title = f"Explode Tags List V{i}"
                desc = f"Given product tags DataFrame `df1`, explode the `tags` array column to create a new row for each tag. The result should contain `product_id` and the exploded tag named `tag` with ID suffix {i}."
                concepts = "explode, select"
                hints = "Use `from pyspark.sql.functions import explode` and select product_id and explode(tags)."
            elif cat == "Window Functions":
                title = f"Rank Users by Score V{i}"
                desc = "Given scores DataFrame `df1`, calculate the rank of each user within their `group` based on `score` descending. Name the new rank column `rank`."
                concepts = "Window, rank, partitionBy, orderBy"
                hints = "Use `Window.partitionBy('group').orderBy(col('score').desc())` and apply `rank().over(windowSpec)`."
            elif cat == "Data Cleaning & Null Handling":
                title = f"Handle Null Scores V{i}"
                desc = "Given user scores DataFrame `df1`, fill any missing (null) values in the `score` column with a dynamically set default value."
                concepts = "fillna, na.fill"
                hints = "Use `df1.fillna(fill_val, subset=['score'])`."
            elif cat == "Performance & Optimization":
                title = f"Repartition DataFrame V{i}"
                desc = "Given input DataFrame `df1`, repartition it to a dynamically set number of partitions using `.repartition()`. Return the repartitioned DataFrame."
                concepts = "repartition"
                hints = "Use `df1.repartition(partitions)`."
            elif cat == "Array & Map Operations":
                title = f"Filter Array Contains V{i}"
                desc = f"Given user interests DataFrame `df1` containing an array column `interests`, filter rows where the array contains the value 'sports_{i}'."
                concepts = "array_contains, filter"
                hints = f"Use `from pyspark.sql.functions import array_contains` and `df1.filter(array_contains(df1.interests, 'sports_{i}'))`."
            elif cat == "User Defined Functions (UDFs)":
                title = f"Custom Celsius conversion UDF V{i}"
                desc = "Define or use a UDF to add a dynamically set value to the temperature values in Celsius column `temp_c`. The result should be named `new_temp`."
                concepts = "udf, withColumn"
                hints = "Define a Python function, register it as a udf: `add_val_udf = udf(lambda x: x + val, IntegerType())` and apply it."

            save_problem({
                "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": comparison_mode
            })
            
            clear_old_data(prob_id)
            save_problem({
                "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": comparison_mode
            })

            # Generate 10 test cases
            for tc_idx in range(1, 11):
                input_dict = {}
                expected = []
                
                if cat == "Filtering & Sorting":
                    val = i * 100
                    # Create unique transactions for each test case
                    input_dict["df1"] = [
                        {"transaction_id": 100 * tc_idx + 1, "amount": val - 50, "user": f"UserA_{tc_idx}"},
                        {"transaction_id": 100 * tc_idx + 2, "amount": val + 150 + tc_idx, "user": f"UserB_{tc_idx}"},
                        {"transaction_id": 100 * tc_idx + 3, "amount": val + 10 * tc_idx, "user": f"UserC_{tc_idx}"}
                    ]
                    expected = [
                        {"transaction_id": 100 * tc_idx + 2, "amount": val + 150 + tc_idx, "user": f"UserB_{tc_idx}"},
                        {"transaction_id": 100 * tc_idx + 3, "amount": val + 10 * tc_idx, "user": f"UserC_{tc_idx}"}
                    ]
                    # Sort expected by transaction_id
                    expected = sorted(expected, key=lambda x: x["transaction_id"])
                    
                elif cat == "Date & String":
                    suffix = f"_{i}_tc{tc_idx}"
                    input_dict["df1"] = [
                        {"user_id": 1, "email": f"alice_{tc_idx}@gmail.com"},
                        {"user_id": 2, "email": f"bob_{tc_idx}@yahoo.com"}
                    ]
                    expected = [
                        {"user_id": 1, "username": f"alice_{tc_idx}{suffix}"},
                        {"user_id": 2, "username": f"bob_{tc_idx}{suffix}"}
                    ]
                    
                elif cat == "Aggregations":
                    threshold = i * 2 + tc_idx
                    input_dict["df1"] = [
                        {"category": "Sports", "points": threshold + 1},
                        {"category": "Sports", "points": tc_idx},
                        {"category": "Music", "points": threshold - 5}
                    ]
                    expected = [
                        {"category": "Sports", "total_points": threshold + 1 + tc_idx}
                    ]
                    
                elif cat == "Joins":
                    input_dict["df1"] = [
                        {"product_id": 1, "sales": 100 + i + tc_idx},
                        {"product_id": 2, "sales": 50 + tc_idx}
                    ]
                    input_dict["df2"] = [
                        {"product_id": 1, "category": f"Electronics_{tc_idx}"},
                        {"product_id": 3, "category": f"Books_{tc_idx}"}
                    ]
                    expected = [
                        {"product_id": 1, "sales": 100 + i + tc_idx, "category": f"Electronics_{tc_idx}"}
                    ]
                    
                elif cat == "Advanced Nested & Pivot":
                    input_dict["df1"] = [
                        {"product_id": i * 10 + tc_idx, "tags": ["sale", f"tag_{tc_idx}"]}
                    ]
                    expected = [
                        {"product_id": i * 10 + tc_idx, "tag": "sale"},
                        {"product_id": i * 10 + tc_idx, "tag": f"tag_{tc_idx}"}
                    ]
                    
                elif cat == "Window Functions":
                    input_dict["df1"] = [
                        {"group": "A", "score": 100 + i + tc_idx, "user_id": 1},
                        {"group": "A", "score": 90 + i + tc_idx, "user_id": 2}
                    ]
                    expected = [
                        {"group": "A", "score": 100 + i + tc_idx, "user_id": 1, "rank": 1},
                        {"group": "A", "score": 90 + i + tc_idx, "user_id": 2, "rank": 2}
                    ]
                    
                elif cat == "Data Cleaning & Null Handling":
                    fill_val = i + tc_idx
                    input_dict["df1"] = [
                        {"user_id": 1, "score": None},
                        {"user_id": 2, "score": 85.0 + tc_idx}
                    ]
                    expected = [
                        {"user_id": 1, "score": float(fill_val)},
                        {"user_id": 2, "score": 85.0 + tc_idx}
                    ]
                    
                elif cat == "Performance & Optimization":
                    # repartition doesn't change content, just partitioning
                    input_dict["df1"] = [
                        {"id": 1, "val": i + tc_idx},
                        {"id": 2, "val": i + tc_idx + 1}
                    ]
                    expected = [
                        {"id": 1, "val": i + tc_idx},
                        {"id": 2, "val": i + tc_idx + 1}
                    ]
                    
                elif cat == "Array & Map Operations":
                    input_dict["df1"] = [
                        {"user_id": 1, "interests": [f"sports_{i}", f"music_{tc_idx}"]},
                        {"user_id": 2, "interests": [f"music_{tc_idx}", "gaming"]}
                    ]
                    expected = [
                        {"user_id": 1, "interests": [f"sports_{i}", f"music_{tc_idx}"]}
                    ]
                    
                elif cat == "User Defined Functions (UDFs)":
                    val = i + tc_idx
                    input_dict["df1"] = [
                        {"city": "CityA", "temp_c": 20 + tc_idx},
                        {"city": "CityB", "temp_c": 15 + tc_idx}
                    ]
                    expected = [
                        {"city": "CityA", "temp_c": 20 + tc_idx, "new_temp": 20 + tc_idx + val},
                        {"city": "CityB", "temp_c": 15 + tc_idx, "new_temp": 15 + tc_idx + val}
                    ]
                
                save_testcase(prob_id, input_dict, expected, tc_idx, comparison_mode)

if __name__ == "__main__":
    generate_all()
    print("Done! 1000 problems generated, each with 10 test cases.")
