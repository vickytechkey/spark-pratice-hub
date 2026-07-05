import pandas as pd
import sqlite3
import os
import json
import ast
from database import db

def import_from_excel(file_path):
    """
    Imports problems, test cases, and datasets from an Excel file.
    
    The Excel workbook should have sheets:
    1. 'Problems' -> id, title, difficulty, category, description, concepts, hints, comparison_mode
    2. 'TestCases' -> problem_id, input_datasets, expected_output_dataset, comparison_mode
    3. 'Datasets' -> name, type, data (JSON string representation of lists of dicts, e.g. [{"id":1,"name":"Alice"}])
    """
    db.init_db()
    
    # Read Sheets
    try:
        xl = pd.ExcelFile(file_path)
    except Exception as e:
        return False, f"Failed to open Excel file: {str(e)}"
        
    required_sheets = ["Problems", "TestCases", "Datasets"]
    for sheet in required_sheets:
        if sheet not in xl.sheet_names:
            return False, f"Missing required sheet: {sheet}"
            
    try:
        # Load Datasets
        df_datasets = xl.parse("Datasets")
        os.makedirs("datasets", exist_ok=True)
        
        for _, row in df_datasets.iterrows():
            name = str(row["name"]).strip()
            file_type = str(row["type"]).strip().upper()
            raw_data = row["data"]
            
            # Parse data
            if isinstance(raw_data, str):
                try:
                    data_list = json.loads(raw_data)
                except json.JSONDecodeError:
                    try:
                        data_list = ast.literal_eval(raw_data)
                    except Exception:
                        return False, f"Invalid JSON/Literal data format for dataset '{name}'"
            elif isinstance(raw_data, list):
                data_list = raw_data
            else:
                data_list = []
                
            df_data = pd.DataFrame(data_list)
            
            # Save dataset locally
            target_path = ""
            if file_type == "CSV":
                target_path = f"datasets/{name}.csv"
                df_data.to_csv(target_path, index=False)
            elif file_type == "PARQUET":
                target_path = f"datasets/{name}.parquet"
                df_data.to_parquet(target_path, index=False)
            elif file_type == "JSON":
                target_path = f"datasets/{name}.json"
                df_data.to_json(target_path, orient="records", indent=2)
            elif file_type == "EXCEL":
                target_path = f"datasets/{name}.xlsx"
                df_data.to_excel(target_path, index=False)
            else:
                # Default to CSV
                file_type = "CSV"
                target_path = f"datasets/{name}.csv"
                df_data.to_csv(target_path, index=False)
                
            # Register in database
            db.add_dataset(name, file_type, target_path)
            
        # Load Problems
        df_problems = xl.parse("Problems")
        for _, row in df_problems.iterrows():
            prob_id = str(row["id"]).strip()
            title = str(row["title"]).strip()
            difficulty = str(row["difficulty"]).strip()
            category = str(row["category"]).strip()
            description = str(row["description"]).strip()
            concepts = str(row.get("concepts", ""))
            hints = str(row.get("hints", ""))
            comparison_mode = str(row.get("comparison_mode", "Exact"))
            
            db.add_problem(prob_id, title, difficulty, category, description, concepts, hints, comparison_mode)
            
        # Load Test Cases
        df_testcases = xl.parse("TestCases")
        
        # Clear existing test cases for these imported problems to prevent duplication
        conn = db.get_connection()
        cursor = conn.cursor()
        imported_problem_ids = df_problems["id"].astype(str).tolist()
        placeholders = ",".join("?" for _ in imported_problem_ids)
        cursor.execute(f"DELETE FROM test_cases WHERE problem_id IN ({placeholders})", imported_problem_ids)
        conn.commit()
        conn.close()
        
        for _, row in df_testcases.iterrows():
            prob_id = str(row["problem_id"]).strip()
            input_datasets_str = str(row["input_datasets"]).strip()
            expected_output = str(row["expected_output_dataset"]).strip()
            comp_mode = row.get("comparison_mode")
            if pd.isna(comp_mode):
                comp_mode = None
            else:
                comp_mode = str(comp_mode).strip()
                
            # Parse input datasets mapping (e.g. df1:customer_data,df2:transaction_data)
            # which maps key to registered dataset name
            input_mappings = {}
            for item in input_datasets_str.split(","):
                if ":" in item:
                    key, val = item.split(":", 1)
                    input_mappings[key.strip()] = val.strip()
                else:
                    input_mappings[item.strip()] = item.strip()
                    
            db.add_test_case(prob_id, input_mappings, expected_output, comp_mode)
            
        return True, f"Successfully imported {len(df_problems)} problems and {len(df_datasets)} datasets."
        
    except Exception as e:
        return False, f"Error during import: {str(e)}"
