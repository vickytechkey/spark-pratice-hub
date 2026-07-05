import streamlit as st

def show():
    st.markdown("<h1 style='color: #ff4b4b;'>📖 Understand Me - Platform Guide</h1>", unsafe_allow_html=True)
    st.write("Welcome! This detailed guide explains how the Spark Practice Hub compiles your code, validates correctness, measures execution performance, and allows custom configuration.")
    
    st.write("---")
    
    # Section 1
    st.subheader("📥 1. How Test Cases Work")
    st.markdown("""
    When you run a solution in the **Practice Sandbox**, the execution engine prepares the environment:
    
    1. **Inputs Parameter (`inputs`):** The second parameter in your `solve(spark, inputs)` function is a standard Python dictionary.
       * Keys (e.g. `'df1'`, `'df2'`) represent the input DataFrame names.
       * Values are the active **PySpark DataFrames** pre-loaded by the engine.
       * *Example access:* `df = inputs['df1']`
       
    2. **Expected Output Validation:** Once your code executes and returns a DataFrame, it is compared against the pre-loaded expected output DataFrame using one of the following assertion modes:
    """)
    
    col_tc1, col_tc2 = st.columns(2)
    with col_tc1:
        st.info("""
        **🔍 Exact Comparison Mode**
        * **How it works:** Sorts both your actual DataFrame and the expected DataFrame by all columns, then collects and compares every row sequentially.
        * **Best for:** Ordered records, direct value matching.
        """)
        st.info("""
        **🔄 Ignore Row Order Mode**
        * **How it works:** Compares row counts first. Then computes mutual differences: `actual.subtract(expected).count() == 0` and `expected.subtract(actual).count() == 0`.
        * **Best for:** Unordered query results (e.g., group-by results without sorting).
        """)
    with col_tc2:
        st.info("""
        **📐 Schema Only Mode**
        * **How it works:** Inspects only the column names and data types. Row content is not compared.
        * **Best for:** Verifying schema compatibility/transformations.
        """)
        st.info("""
        **🔢 Row Count Mode**
        * **How it works:** Simply validates if the number of rows matches.
        * **Best for:** Fast sizing comparisons.
        """)
        
    st.write("---")
    
    # Section 2
    st.subheader("📊 2. How Performance Metrics are Calculated")
    st.markdown("""
    To give you feedback on your Spark code's efficiency, the execution runner collects diagnostic parameters:
    
    * **Runtime (ms):** Measured using high-precision timers (`time.perf_counter()`) wrapped directly around your `solve()` call and a triggering DataFrame action (like `.count()`).
    * **Spark Jobs:** Total count of active computations triggered.
    * **Spark Stages:** Steps/splits in the execution DAG (e.g., Map vs. Reduce stages).
    * **Spark Tasks:** Number of parallel execution threads/tasks spun up.
    
    **How we capture Spark Internals:**
    We assign a unique **Job Group ID** (UUID) to the Spark context (`spark.sparkContext.setJobGroup()`) before running each test case. After completion, we query the `spark.sparkContext.statusTracker()` to retrieve details for that specific Job Group.
    """)
    
    st.write("---")
    
    # Section 3
    st.subheader("⚡ 3. Tuning Spark Configurations (Top to Bottom)")
    st.markdown("""
    You can tune Spark execution configurations via the **Spark Execution Profiles** tab:
    
    * **Master URL (`master`):**
      * `local[*]`: Runs Spark locally, spawning worker threads matching your computer's logical cores.
      * `local[2]`: Spawns exactly 2 worker threads.
    * **Driver & Executor Memory (`driver_memory`, `executor_memory`):**
      * Sets heap memory for Spark processes (e.g., `1g`, `2g`, `4g`). Increase this if you face JVM Heap Space OOM errors.
    * **Shuffle Partitions (`shuffle_partitions`):**
      * Configures the number of partitions to use when shuffling data for joins or aggregations. For small practice datasets, keeping this low (e.g., `2` or `4`) prevents Spark from creating 200 empty partitions, drastically speeding up execution.
    * **Adaptive Query Execution (AQE):**
      * Dynamically optimizes query execution plans at runtime based on size statistics.
    * **Broadcast Threshold (`broadcast_threshold`):**
      * Maximum size in bytes for a table that will be broadcast to all worker nodes when performing joins. Set to `-1` to disable broadcast joins.
    """)
    
    # Section 4
    st.subheader("📥 4. Custom Problems and Datasets")
    st.markdown("""
    Want to practice a specific problem? Import it via the **Import Problems** page:
    1. **Download the sample Excel template**.
    2. Fill out the `Problems` (descriptions/metadata), `TestCases` (mappings), and `Datasets` sheets (datasets containing JSON arrays of records).
    3. Upload the spreadsheet. The app automatically compiles and saves the mock datasets to `datasets/` as CSV/JSON/Parquet files and registers the problems in SQLite.
    """)
    
    st.write("---")
    
    # Section 5
    st.subheader("🔍 5. Topic Classification Logic (Weak vs. Strong)")
    st.markdown("""
    The dashboard evaluates all your submissions to classify Spark topics:
    
    *   **⚠️ Weak Spark Topics:** 
        *   Classified if the topic success rate (Solved / Attempts) is **less than 50%**.
        *   OR if you have made **multiple attempts (> 1)** on problems in that topic but solved **0** problems.
        *   *Action:* Target these topics first to improve interview readiness.
    
    *   **💪 Strong Spark Topics:**
        *   Classified if the topic success rate is **80% or higher** (with at least 1 attempt).
        *   *Action:* Keep solving new problems in these categories to maintain familiarity.
        
    *   **⚪ Neutral/Untouched Topics:**
        *   Topics with no attempts yet, or success rates between 50% and 80%.
    """)
