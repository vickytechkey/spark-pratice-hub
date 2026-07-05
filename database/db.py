import sqlite3
import os
import json
import datetime
import yaml

DB_PATH = "database/spark_practice.db"

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. problems table
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
    
    # 2. test_cases table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        input_datasets TEXT NOT NULL, -- JSON object of input_name: dataset_name
        expected_output_dataset TEXT NOT NULL, -- dataset name of expected output
        comparison_mode TEXT,
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)
    
    # 3. datasets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datasets (
        name TEXT PRIMARY KEY,
        type TEXT NOT NULL, -- CSV, Parquet, JSON, Excel
        file_path TEXT NOT NULL
    )
    """)
    
    # 4. submissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        code TEXT NOT NULL,
        status TEXT NOT NULL, -- PASS, FAIL, ERROR
        execution_time_ms INTEGER,
        metrics TEXT, -- JSON structure of job metrics
        error_message TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
    )
    """)
    
    # 5. spark_profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS spark_profiles (
        name TEXT PRIMARY KEY,
        master TEXT NOT NULL,
        driver_memory TEXT NOT NULL,
        executor_memory TEXT NOT NULL,
        executor_cores INTEGER NOT NULL,
        shuffle_partitions INTEGER NOT NULL,
        adaptive_query_execution INTEGER DEFAULT 1,
        broadcast_threshold INTEGER DEFAULT 10485760,
        serializer TEXT DEFAULT 'org.apache.spark.serializer.KryoSerializer',
        default_parallelism INTEGER DEFAULT 2,
        extra_configs TEXT -- JSON structure
    )
    """)
    
    # 6. goals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL, -- Daily, Weekly, Monthly, Streak
        target INTEGER NOT NULL,
        progress INTEGER DEFAULT 0,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL
    )
    """)
    
    # 7. daily_activity table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_activity (
        date TEXT PRIMARY KEY, -- YYYY-MM-DD
        attempts INTEGER DEFAULT 0,
        solved INTEGER DEFAULT 0
    )
    """)
    
    # Load default profiles from YAML if they don't exist
    if os.path.exists("config/config.yaml"):
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
            if "spark_profiles" in config:
                for name, p in config["spark_profiles"].items():
                    cursor.execute("SELECT 1 FROM spark_profiles WHERE name = ?", (name,))
                    if not cursor.fetchone():
                        cursor.execute("""
                        INSERT INTO spark_profiles (
                            name, master, driver_memory, executor_memory, executor_cores, 
                            shuffle_partitions, adaptive_query_execution, broadcast_threshold, 
                            serializer, default_parallelism
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            name, p.get("master", "local[*]"), p.get("driver_memory", "1g"),
                            p.get("executor_memory", "1g"), p.get("executor_cores", 1),
                            p.get("shuffle_partitions", 2), 1 if p.get("adaptive_query_execution", True) else 0,
                            p.get("broadcast_threshold", 10485760), p.get("serializer", "org.apache.spark.serializer.KryoSerializer"),
                            p.get("default_parallelism", 2)
                        ))
                        
    conn.commit()
    conn.close()

# CRUD operations

# Problems
def add_problem(problem_id, title, difficulty, category, description, concepts="", hints="", comparison_mode="Exact"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO problems (id, title, difficulty, category, description, concepts, hints, comparison_mode)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (problem_id, title, difficulty, category, description, concepts, hints, comparison_mode))
    conn.commit()
    conn.close()

def get_problems(search="", difficulty="All", category="All"):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM problems WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR concepts LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if difficulty != "All":
        query += " AND difficulty = ?"
        params.append(difficulty)
    if category != "All":
        query += " AND category = ?"
        params.append(category)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_problem(problem_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM problems WHERE id = ?", (problem_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Test Cases
def add_test_case(problem_id, input_datasets, expected_output_dataset, comparison_mode=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO test_cases (problem_id, input_datasets, expected_output_dataset, comparison_mode)
    VALUES (?, ?, ?, ?)
    """, (problem_id, json.dumps(input_datasets), expected_output_dataset, comparison_mode))
    conn.commit()
    conn.close()

def get_test_cases(problem_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM test_cases WHERE problem_id = ?", (problem_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["input_datasets"] = json.loads(d["input_datasets"])
        result.append(d)
    return result

# Datasets
def add_dataset(name, file_type, file_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO datasets (name, type, file_path)
    VALUES (?, ?, ?)
    """, (name, file_type, file_path))
    conn.commit()
    conn.close()

def get_dataset(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasets WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Submissions
def add_submission(problem_id, code, status, execution_time_ms, metrics=None, error_message=None):
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO submissions (problem_id, code, status, execution_time_ms, metrics, error_message, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (problem_id, code, status, execution_time_ms, json.dumps(metrics) if metrics else None, error_message, now_str))
    
    # Update daily activity
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT * FROM daily_activity WHERE date = ?", (today_str,))
    activity = cursor.fetchone()
    if activity:
        attempts = activity["attempts"] + 1
        solved = activity["solved"] + (1 if status == "PASS" else 0)
        cursor.execute("UPDATE daily_activity SET attempts = ?, solved = ? WHERE date = ?", (attempts, solved, today_str))
    else:
        solved = 1 if status == "PASS" else 0
        cursor.execute("INSERT INTO daily_activity (date, attempts, solved) VALUES (?, 1, ?)", (today_str, solved))
        
    conn.commit()
    conn.close()

def get_submissions(problem_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if problem_id:
        cursor.execute("SELECT * FROM submissions WHERE problem_id = ? ORDER BY timestamp DESC", (problem_id,))
    else:
        cursor.execute("SELECT * FROM submissions ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["metrics"] = json.loads(d["metrics"]) if d["metrics"] else None
        result.append(d)
    return result

# Spark Profiles
def get_profiles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM spark_profiles")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_profile(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM spark_profiles WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_profile(name, master, driver_memory, executor_memory, executor_cores, shuffle_partitions, aeq=1, broadcast_threshold=10485760, serializer="org.apache.spark.serializer.KryoSerializer", default_parallelism=2, extra_configs=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO spark_profiles (name, master, driver_memory, executor_memory, executor_cores, shuffle_partitions, adaptive_query_execution, broadcast_threshold, serializer, default_parallelism, extra_configs)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, master, driver_memory, executor_memory, executor_cores, shuffle_partitions, aeq, broadcast_threshold, serializer, default_parallelism, json.dumps(extra_configs) if extra_configs else None))
    conn.commit()
    conn.close()

def delete_profile(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM spark_profiles WHERE name = ?", (name,))
    conn.commit()
    conn.close()

# Dashboard Stats & Streak
def get_streak_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, solved FROM daily_activity WHERE solved > 0 ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {"current_streak": 0, "longest_streak": 0}
        
    dates = [datetime.datetime.strptime(r["date"], "%Y-%m-%d").date() for r in rows]
    
    # Calculate current streak
    current_streak = 0
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    
    if dates[0] == today or dates[0] == yesterday:
        current_streak = 1
        for i in range(1, len(dates)):
            if (dates[i-1] - dates[i]).days == 1:
                current_streak += 1
            elif (dates[i-1] - dates[i]).days == 0:
                continue
            else:
                break
    else:
        current_streak = 0
        
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    unique_dates = sorted(list(set(dates)), reverse=True)
    if unique_dates:
        temp_streak = 1
        longest_streak = 1
        for i in range(1, len(unique_dates)):
            if (unique_dates[i-1] - unique_dates[i]).days == 1:
                temp_streak += 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak
            else:
                temp_streak = 1
                
    return {"current_streak": current_streak, "longest_streak": longest_streak}

def get_daily_activity():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, attempts, solved FROM daily_activity")
    rows = cursor.fetchall()
    conn.close()
    return {r["date"]: {"attempts": r["attempts"], "solved": r["solved"]} for r in rows}

# Goals
def get_goals():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_goal(goal_type, target, progress, start_date, end_date, goal_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if goal_id:
        cursor.execute("""
        UPDATE goals SET type = ?, target = ?, progress = ?, start_date = ?, end_date = ? WHERE id = ?
        """, (goal_type, target, progress, start_date, end_date, goal_id))
    else:
        cursor.execute("""
        INSERT INTO goals (type, target, progress, start_date, end_date) VALUES (?, ?, ?, ?, ?)
        """, (goal_type, target, progress, start_date, end_date))
    conn.commit()
    conn.close()

def delete_goal(goal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()

