# Spark Practice Hub - Product Requirements Document (PRD)

Version: 1.0

## Vision

Build a **desktop-first PySpark practice platform** for interview
preparation. The application behaves like a local coding judge combined
with a Spark performance laboratory.

## Goals

-   Practice one PySpark problem every day.
-   Maintain a daily streak.
-   Validate solutions against test cases.
-   Learn Spark performance and execution internals.
-   Track long-term progress.

## Technology Stack

-   UI: Streamlit
-   Language: Python 3.13
-   Processing: PySpark
-   Database: SQLite
-   Import/Export: pandas + openpyxl
-   Charts: Plotly
-   Configuration: YAML
-   Local storage only (no authentication)

## Folder Structure

``` text
spark-practice-hub/
├── app.py
├── config/
├── database/
├── problems/
├── datasets/
├── solutions/
├── uploads/
├── exports/
├── reports/
├── engine/
├── ui/
├── tests/
├── logs/
└── README.md
```

# Core Modules

## 1. Dashboard

-   Current streak
-   Longest streak
-   Problems solved
-   Problems attempted
-   Success rate
-   Coding hours
-   Spark jobs executed
-   Today's mission
-   Monthly goal progress
-   GitHub-style contribution heatmap

## 2. Problem Bank

Each problem contains: - ID - Title - Difficulty - Category -
Description - Concepts - Hints - Dataset references - Test cases

Supported dataset formats: - CSV - Excel - JSON - Parquet

## 3. Problem Import

Import from Excel workbook.

Sheets: - Problems - TestCases - Datasets

## 4. Code Editor

User implements:

``` python
def solve(spark, inputs):
    ...
    return dataframe
```

The application supplies SparkSession and input DataFrames.

## 5. Test Runner

Workflow:

1.  Load selected problem
2.  Create SparkSession
3.  Apply selected Spark profile
4.  Load datasets
5.  Execute solve()
6.  Compare with expected output
7.  Record metrics
8.  Save history

Comparison modes: - Exact - Ignore row order - Schema only - Row count -
Custom validator

## 6. Spark Profiles

Example profiles: - Laptop - Interview - Large Dataset

Configurable settings: - master - driver memory - executor memory -
executor cores - shuffle partitions - adaptive query execution -
broadcast threshold - serializer - default parallelism

## 7. Performance Metrics

For every execution capture: - Execution time - Jobs - Stages - Tasks -
Input rows - Output rows - Shuffle read/write - Spill - Driver memory -
Executor memory - Spark configuration used

Future: - Spark UI integration - Explain plan - Benchmark mode

## 8. History

Store: - Submission time - Code version - Pass/fail - Attempts -
Runtime - Metrics

Allow export: - CSV - Excel - ZIP

## 9. Statistics

Show: - Solved by difficulty - Solved by topic - Coding hours - Success
rate - Average runtime - Weak topics - Monthly trend

## 10. Goals

Supported: - Daily goal - Weekly goal - Monthly goal - Topic goal -
Streak goal

Dashboard should display: - Current mission - Remaining work - On-track
status

## 11. Contribution Graph

Heatmap similar to GitHub.

Legend: - White = no activity - Green = attempted - Yellow = solved -
Blue = multiple solved - Purple = personal best

## 12. Achievements

Examples: - First problem - 10 problems - 50 problems - 100 problems -
7-day streak - 30-day streak - 100-day streak - First hard problem - 100
Spark jobs - 100% pass rate

## 13. Database

Tables: - problems - test_cases - datasets - submissions - solutions -
spark_profiles - goals - achievements - daily_activity - settings

## MVP Scope

-   Streamlit UI
-   SQLite
-   Import problems
-   Browse/search
-   Code editor
-   Run PySpark solution
-   Execute multiple test cases
-   Pass/fail report
-   Configurable Spark resources
-   Save history
-   Export history
-   Dashboard
-   Daily streak
-   Monthly goal
-   Contribution graph

## Future Releases

### Version 2

-   Spark UI metrics
-   Explain plans
-   Benchmark mode
-   Resource charts
-   Version comparison

### Version 3

-   AI hints
-   Automatic difficulty recommendations
-   Personalized learning roadmap

## Definition of Success

The application should motivate solving at least **one PySpark problem
every day** while providing meaningful correctness and performance
feedback.
