import streamlit as st
import pandas as pd
import io
import os
from engine import importer
from database import db

def generate_sample_excel():
    # 1. Problems sheet
    df_problems = pd.DataFrame([
        {
            "id": "SPK-001",
            "title": "Filter Active Customers",
            "difficulty": "Easy",
            "category": "Filter & Select",
            "description": "Given a customer DataFrame, filter out customers who are active (status = 'active') and reside in 'New York'. Select only their customer_id and customer_name.",
            "concepts": "filter, select, show",
            "hints": "Use .filter() with multiple conditions joined by &; Use .select() to get specific columns.",
            "comparison_mode": "Exact"
        },
        {
            "id": "SPK-002",
            "title": "Total Transaction Volume by Customer",
            "difficulty": "Medium",
            "category": "Aggregation",
            "description": "Calculate the total transaction amount for each customer. Return customer_id and total_amount. Sort the output in descending order of total_amount.",
            "concepts": "groupBy, sum, agg, sort",
            "hints": "Group by customer_id; Aggregate sum(amount); Sort by total_amount descending.",
            "comparison_mode": "Ignore row order"
        }
    ])
    
    # 2. TestCases sheet - demonstrating 3 test cases for SPK-001
    df_testcases = pd.DataFrame([
        # SPK-001 Test Cases
        {
            "problem_id": "SPK-001",
            "input_datasets": "df1:cust_data_tc1",
            "expected_output_dataset": "exp_active_tc1",
            "comparison_mode": "Exact"
        },
        {
            "problem_id": "SPK-001",
            "input_datasets": "df1:cust_data_tc2",
            "expected_output_dataset": "exp_active_tc2",
            "comparison_mode": "Exact"
        },
        {
            "problem_id": "SPK-001",
            "input_datasets": "df1:cust_data_tc3",
            "expected_output_dataset": "exp_active_tc3",
            "comparison_mode": "Exact"
        },
        # SPK-002 Test Case
        {
            "problem_id": "SPK-002",
            "input_datasets": "df1:trans_data_tc1",
            "expected_output_dataset": "exp_volumes_tc1",
            "comparison_mode": "Ignore row order"
        }
    ])
    
    # 3. Datasets sheet - defining actual mock data for each test case
    # SPK-001 Data
    cust_tc1 = [
        {"customer_id": 1, "customer_name": "Alice", "status": "active", "city": "New York"},
        {"customer_id": 2, "customer_name": "Bob", "status": "inactive", "city": "New York"}
    ]
    exp_tc1 = [{"customer_id": 1, "customer_name": "Alice"}]
    
    cust_tc2 = [
        {"customer_id": 3, "customer_name": "Charlie", "status": "active", "city": "Los Angeles"},
        {"customer_id": 4, "customer_name": "David", "status": "active", "city": "New York"}
    ]
    exp_tc2 = [{"customer_id": 4, "customer_name": "David"}]
    
    cust_tc3 = [
        {"customer_id": 5, "customer_name": "Eve", "status": "active", "city": "New York"}
    ]
    exp_tc3 = [{"customer_id": 5, "customer_name": "Eve"}]
    
    # SPK-002 Data
    trans_tc1 = [
        {"transaction_id": 101, "customer_id": 1, "amount": 150.0},
        {"transaction_id": 102, "customer_id": 2, "amount": 200.0},
        {"transaction_id": 103, "customer_id": 1, "amount": 50.0}
    ]
    exp_vol_tc1 = [
        {"customer_id": 1, "total_amount": 200.0},
        {"customer_id": 2, "total_amount": 200.0}
    ]
    
    df_datasets = pd.DataFrame([
        {"name": "cust_data_tc1", "type": "CSV", "data": str(cust_tc1)},
        {"name": "exp_active_tc1", "type": "CSV", "data": str(exp_tc1)},
        {"name": "cust_data_tc2", "type": "CSV", "data": str(cust_tc2)},
        {"name": "exp_active_tc2", "type": "CSV", "data": str(exp_tc2)},
        {"name": "cust_data_tc3", "type": "CSV", "data": str(cust_tc3)},
        {"name": "exp_active_tc3", "type": "CSV", "data": str(exp_tc3)},
        {"name": "trans_data_tc1", "type": "CSV", "data": str(trans_tc1)},
        {"name": "exp_volumes_tc1", "type": "CSV", "data": str(exp_vol_tc1)}
    ])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_problems.to_excel(writer, sheet_name="Problems", index=False)
        df_testcases.to_excel(writer, sheet_name="TestCases", index=False)
        df_datasets.to_excel(writer, sheet_name="Datasets", index=False)
        
    return output.getvalue()

def show():
    st.title("📥 Problem Import & Administration")
    st.write("Import PySpark coding problems and datasets from Excel workbooks.")
    
    # 1. Download sample Excel workbook
    st.subheader("1. Download template Excel workbook")
    st.write("Use this template to format your own problems, test cases, and mock datasets.")
    
    excel_data = generate_sample_excel()
    st.download_button(
        label="Download template Excel file",
        data=excel_data,
        file_name="spark_problems_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    with st.expander("📖 Template Sheet Specifications & Schema Guidelines"):
        st.markdown("""
        The Excel workbook must contain exactly three sheets:
        
        ### 1. `Problems` Sheet
        Contains the problem definitions:
        *   **`id`**: Unique alphanumeric ID (e.g. `SPK-001`).
        *   **`title`**: Problem title.
        *   **`difficulty`**: `Easy`, `Medium`, or `Hard`.
        *   **`category`**: Topic category (e.g. `Filter & Select`, `Aggregation`, `Joins`).
        *   **`description`**: Multi-line markdown text describing the problem goal and inputs.
        *   **`concepts`**: Comma-separated Spark functions (e.g., `filter, select`).
        *   **`hints`**: Semicolon-separated hints list.
        *   **`comparison_mode`**: Defaults to `Exact`. Options: `Exact`, `Ignore row order`, `Schema only`, `Row count`.
        
        ---
        
        ### 2. `TestCases` Sheet
        Links problems to input datasets and expected output:
        *   **`problem_id`**: Alphanumeric ID of the problem (matches `id` in `Problems`).
        *   **`input_datasets`**: Comma-separated mapping of `variable_name:dataset_name` (e.g. `df1:cust_data_tc1` maps input dictionary key `df1` to data table `cust_data_tc1`).
        *   **`expected_output_dataset`**: Name of the expected result dataset (e.g. `exp_active_tc1`).
        *   **`comparison_mode`**: (Optional) Override comparison rule (e.g. `Exact`).
        
        ---
        
        ### 3. `Datasets` Sheet
        Provides mock data for inputs and outputs:
        *   **`name`**: Unique name reference used in TestCases (e.g. `cust_data_tc1`).
        *   **`type`**: Format type: `CSV`, `JSON`, `PARQUET`, or `EXCEL`.
        *   **`data`**: Raw JSON representation of data records:
            ```json
            [
              {"customer_id": 1, "customer_name": "Alice", "status": "active", "city": "New York"},
              {"customer_id": 2, "customer_name": "Bob", "status": "inactive", "city": "New York"}
            ]
            ```
        """)
        
    # 2. Upload file
    st.write("---")
    st.subheader("2. Upload completed workbook")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    if uploaded_file is not None:
        os.makedirs("uploads", exist_ok=True)
        temp_path = f"uploads/{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.write("Processing workbook...")
        success, msg = importer.import_from_excel(temp_path)
        
        if success:
            st.success(msg)
            # Remove temp file
            try:
                os.remove(temp_path)
            except Exception:
                pass
        else:
            st.error(msg)
            
    # 3. DB Cleanup / Maintenance
    st.write("---")
    st.subheader("3. Maintenance & Actions")
    if st.button("Reset Database & Reinitialize Default Profiles", type="primary"):
        try:
            if os.path.exists(db.DB_PATH):
                os.remove(db.DB_PATH)
            db.init_db()
            st.success("Database reset complete. Reloading default spark profiles.")
            st.rerun()
        except Exception as e:
            st.error(f"Error resetting database: {str(e)}")
