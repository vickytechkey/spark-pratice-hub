import os
import json
import sqlite3
import random

# We'll use a fixed seed for reproducible generation
random.seed(42)

DB_PATH = "database/spark_practice.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ensure tables exist
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

def save_problem_and_testcase(prob, input_data_dict, expected_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Save datasets
    input_mappings = {}
    for key, data in input_data_dict.items():
        ds_name = f"{prob['id']}_{key}"
        save_dataset(ds_name, data)
        input_mappings[key] = ds_name
        
    exp_ds_name = f"{prob['id']}_expected"
    save_dataset(exp_ds_name, expected_data)
    
    # Save problem
    cursor.execute("""
    INSERT OR REPLACE INTO problems (id, title, difficulty, category, description, concepts, hints, comparison_mode)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (prob['id'], prob['title'], prob['difficulty'], prob['category'], prob['description'], prob['concepts'], prob['hints'], prob['comparison_mode']))
    
    # Save testcase (delete old first to avoid duplicate)
    cursor.execute("DELETE FROM test_cases WHERE problem_id = ?", (prob['id'],))
    cursor.execute("""
    INSERT INTO test_cases (problem_id, input_datasets, expected_output_dataset, comparison_mode)
    VALUES (?, ?, ?, ?)
    """, (prob['id'], json.dumps(input_mappings), exp_ds_name, prob['comparison_mode']))
    
    conn.commit()
    conn.close()

# Let's generate 100 problems for each of the 10 categories
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

category_prefixes = {
    "Filtering & Sorting": "FIL",
    "Date & String": "DTE",
    "Aggregations": "AGG",
    "Joins": "JOI",
    "Advanced Nested & Pivot": "ADV",
    "Window Functions": "WIN",
    "Data Cleaning & Null Handling": "CLE",
    "Performance & Optimization": "PER",
    "Array & Map Operations": "ARR",
    "User Defined Functions (UDFs)": "USE"
}

EXAMPLES_MD = """

### Example 1
**Input (`df1`):**
| user_id | score |
| :--- | :--- |
| 1 | null |
| 2 | 80.0 |
| 3 | 90.0 |
| 4 | null |
| 5 | 70.0 |

**Expected Output:**
| user_id | score |
| :--- | :--- |
| 1 | 80.0 |
| 2 | 80.0 |
| 3 | 90.0 |
| 4 | 80.0 |
| 5 | 70.0 |

*(Average score of non-nulls `[80.0, 90.0, 70.0]` is `80.0`)*

### Example 2
**Input (`df1`):**
| user_id | score |
| :--- | :--- |
| 10 | 100.0 |
| 11 | null |
| 12 | 50.0 |
| 13 | 60.0 |
| 14 | 90.0 |

**Expected Output:**
| user_id | score |
| :--- | :--- |
| 10 | 100.0 |
| 11 | 75.0 |
| 12 | 50.0 |
| 13 | 60.0 |
| 14 | 90.0 |

*(Average score of non-nulls `[100.0, 50.0, 60.0, 90.0]` is `75.0`)*

### Example 3
**Input (`df1`):**
| user_id | score |
| :--- | :--- |
| 20 | null |
| 21 | 95.0 |
| 22 | 85.0 |
| 23 | null |

**Expected Output:**
| user_id | score |
| :--- | :--- |
| 20 | 90.0 |
| 21 | 95.0 |
| 22 | 85.0 |
| 23 | 90.0 |

*(Average score of non-nulls `[95.0, 85.0]` is `90.0`)*
"""

def generate_all():
    init_db()
    
    # Clean up old database entries to prevent duplicate/colliding problems
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for prefix in ["SPK-DAT-", "SPK-DTE-", "SPK-CLE-"]:
        cursor.execute("DELETE FROM test_cases WHERE problem_id LIKE ?", (prefix + "%",))
        cursor.execute("DELETE FROM problems WHERE id LIKE ?", (prefix + "%",))
        cursor.execute("DELETE FROM datasets WHERE name LIKE ?", (prefix + "%",))
    conn.commit()
    conn.close()
    
    for cat in categories:
        print(f"Generating for category: {cat}...")
        for i in range(1, 101):
            prefix = category_prefixes.get(cat, cat[:3].upper())
            prob_id = f"SPK-{prefix}-{i:03d}"
            difficulty = "Easy" if i <= 35 else "Medium" if i <= 80 else "Hard"
            
            # Category-specific template logic
            if cat == "Filtering & Sorting":
                val = i * 100
                title = f"Filter High Value Transactions V{i}"
                desc = f"Given a transaction DataFrame `df1`, filter transactions where the `amount` is strictly greater than {val}. Sort the results by `transaction_id` ascending."
                concepts = "filter, where, orderBy"
                hints = f"Use `df1.filter(df1.amount > {val})` and chain it with `.orderBy('transaction_id')`."
                
                # Mock Data
                input_data = [
                    {"transaction_id": 101, "amount": val - 50, "user": "UserA"},
                    {"transaction_id": 102, "amount": val + 150, "user": "UserB"},
                    {"transaction_id": 103, "amount": val + 10, "user": "UserC"}
                ]
                expected = [
                    {"transaction_id": 102, "amount": val + 150, "user": "UserB"},
                    {"transaction_id": 103, "amount": val + 10, "user": "UserC"}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Exact"
                }, {"df1": input_data}, expected)
                
            elif cat == "Date & String":
                title = f"Clean Domain Names V{i}"
                desc = f"Given user accounts DataFrame `df1`, extract the user name (part before '@') from the `email` column, name the new column `username`, and keep only columns `user_id` and `username`. Append suffix '_{i}_tc' to username."
                concepts = "withColumn, split, select"
                hints = f"Use `split(df1.email, '@')[0]` to extract the name, and concat the suffix '_{i}_tc'."
                
                input_data = [
                    {"user_id": 1, "email": "alice@gmail.com"},
                    {"user_id": 2, "email": "bob@yahoo.com"}
                ]
                expected = [
                    {"user_id": 1, "username": f"alice_{i}_tc"},
                    {"user_id": 2, "username": f"bob_{i}_tc"}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "Aggregations":
                threshold = i * 2
                title = f"Sum Active Points V{i}"
                desc = f"Group the user points DataFrame `df1` by `category`, sum the `points` column naming the result `total_points`, and filter to keep categories where `total_points` is greater than {threshold}."
                concepts = "groupBy, agg, sum, filter"
                hints = f"Use `.groupBy('category').agg(sum('points').alias('total_points')).filter('total_points > {threshold}')`."
                
                input_data = [
                    {"category": "Sports", "points": threshold + 1},
                    {"category": "Sports", "points": 1},
                    {"category": "Music", "points": threshold - 5}
                ]
                expected = [
                    {"category": "Sports", "total_points": threshold + 2}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "Joins":
                title = f"Sales with Category V{i}"
                desc = "Perform an inner join between sales DataFrame `df1` and products DataFrame `df2` on `product_id`. Return all columns from both DataFrames (ensure you do not duplicate the key column)."
                concepts = "join, inner"
                hints = "Use `df1.join(df2, 'product_id')` or specify the join key as a string to avoid duplicated columns."
                
                input1 = [{"product_id": 1, "sales": 100 + i}, {"product_id": 2, "sales": 50}]
                input2 = [{"product_id": 1, "category": "Electronics"}, {"product_id": 3, "category": "Books"}]
                expected = [{"product_id": 1, "sales": 100 + i, "category": "Electronics"}]
                
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input1, "df2": input2}, expected)
                
            elif cat == "Advanced Nested & Pivot":
                title = f"Explode Tags List V{i}"
                desc = f"Given product tags DataFrame `df1`, explode the `tags` array column to create a new row for each tag. The result should contain `product_id` and the exploded tag named `tag` with ID suffix {i}."
                concepts = "explode, select"
                hints = "Use `from pyspark.sql.functions import explode` and select product_id and explode(tags)."
                
                input_data = [
                    {"product_id": i, "tags": ["sale", "new"]}
                ]
                expected = [
                    {"product_id": i, "tag": "sale"},
                    {"product_id": i, "tag": "new"}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "Window Functions":
                title = f"Rank Users by Score V{i}"
                desc = "Given scores DataFrame `df1`, calculate the rank of each user within their `group` based on `score` descending. Name the new rank column `rank`."
                concepts = "Window, rank, partitionBy, orderBy"
                hints = "Use `Window.partitionBy('group').orderBy(col('score').desc())` and apply `rank().over(windowSpec)`."
                
                input_data = [
                    {"group": "A", "score": 100 + i, "user_id": 1},
                    {"group": "A", "score": 90 + i, "user_id": 2}
                ]
                expected = [
                    {"group": "A", "score": 100 + i, "user_id": 1, "rank": 1},
                    {"group": "A", "score": 90 + i, "user_id": 2, "rank": 2}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "Data Cleaning & Null Handling":
                title = f"Handle Null Scores V{i}"
                desc = "Given user scores DataFrame `df1`, fill any missing (null) values in the `score` column with the average score computed dynamically from all non-null scores." + EXAMPLES_MD
                concepts = "fillna, na.fill"
                hints = "Calculate average score first using `df1.select(avg('score')).first()[0]` and fill nulls: `df1.fillna(avg_score, subset=['score'])`."
                
                # Generate 8 rows
                base_score = 70.0 + i
                raw_scores = [
                    base_score + 10.0,
                    None,
                    base_score + 5.0,
                    None,
                    base_score + 15.0,
                    base_score,
                    None,
                    base_score + 20.0
                ]
                avg_val = base_score + 10.0
                
                input_data = []
                expected = []
                for row_idx, score in enumerate(raw_scores, start=1):
                    input_data.append({"user_id": row_idx, "score": score})
                    expected.append({"user_id": row_idx, "score": float(avg_val) if score is None else float(score)})
                    
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "Performance & Optimization":
                partitions = 2 if i % 2 == 0 else 4
                title = f"Repartition DataFrame V{i}"
                desc = f"Given input DataFrame `df1`, repartition it to exactly {partitions} partitions using `.repartition()`. Return the repartitioned DataFrame."
                concepts = "repartition"
                hints = f"Use `df1.repartition({partitions})`. Note that the runner will compare outputs normally."
                
                input_data = [{"id": 1, "val": i}, {"id": 2, "val": i + 1}]
                expected = [{"id": 1, "val": i}, {"id": 2, "val": i + 1}]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "Array & Map Operations":
                val = i
                title = f"Filter Array Contains V{i}"
                desc = f"Given user interests DataFrame `df1` containing an array column `interests`, filter rows where the array contains the value 'sports_{val}'."
                concepts = "array_contains, filter"
                hints = f"Use `from pyspark.sql.functions import array_contains` and `df1.filter(array_contains(df1.interests, 'sports_{val}'))`."
                
                input_data = [
                    {"user_id": 1, "interests": [f"sports_{val}", "music"]},
                    {"user_id": 2, "interests": ["music", "gaming"]}
                ]
                expected = [
                    {"user_id": 1, "interests": [f"sports_{val}", "music"]}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)
                
            elif cat == "User Defined Functions (UDFs)":
                val = i
                title = f"Custom Celsius conversion UDF V{i}"
                desc = f"Define or use a UDF to add {val} to the temperature values in Celsius column `temp_c`. The result should be named `new_temp`."
                concepts = "udf, withColumn"
                hints = f"Define a Python function, register it as a udf: `add_val_udf = udf(lambda x: x + {val}, IntegerType())` and apply it."
                
                input_data = [
                    {"city": "CityA", "temp_c": 20},
                    {"city": "CityB", "temp_c": 15}
                ]
                expected = [
                    {"city": "CityA", "temp_c": 20, "new_temp": 20 + val},
                    {"city": "CityB", "temp_c": 15, "new_temp": 15 + val}
                ]
                save_problem_and_testcase({
                    "id": prob_id, "title": title, "difficulty": difficulty, "category": cat,
                    "description": desc, "concepts": concepts, "hints": hints, "comparison_mode": "Ignore row order"
                }, {"df1": input_data}, expected)

if __name__ == "__main__":
    generate_all()
    print("Done! 1000 problems generated.")
