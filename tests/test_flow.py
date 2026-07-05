import unittest
import os
import sys
import shutil
import json

# Ensure workspace is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from engine import importer, runner
from ui import admin

class TestSparkPracticeHub(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Setup clean test DB and directories
        db.DB_PATH = "database/test_spark_practice.db"
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)
        db.init_db()
        
    @classmethod
    def tearDownClass(cls):
        # Cleanup
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)
        if os.path.exists("datasets"):
            # Don't delete entire datasets directory if user is using it,
            # but delete test ones if possible.
            pass

    def test_database_init(self):
        # Check profiles were inserted
        profiles = db.get_profiles()
        self.assertTrue(len(profiles) > 0)
        
    def test_import_and_execution(self):
        # 1. Generate sample excel
        excel_bytes = admin.generate_sample_excel()
        temp_excel = "tests/temp_test_problems.xlsx"
        os.makedirs("tests", exist_ok=True)
        with open(temp_excel, "wb") as f:
            f.write(excel_bytes)
            
        # 2. Import Excel
        success, msg = importer.import_from_excel(temp_excel)
        self.assertTrue(success, f"Import failed: {msg}")
        
        # Verify DB entries
        problems = db.get_problems()
        self.assertEqual(len(problems), 2)
        
        datasets = [db.get_dataset("cust_data_tc1"), db.get_dataset("exp_active_tc1")]
        for ds in datasets:
            self.assertIsNotNone(ds)
            self.assertTrue(os.path.exists(ds["file_path"]))
            
        # 3. Test Correct Solution
        correct_code = """def solve(spark, inputs):
    df = inputs['df1']
    return df.filter((df.status == 'active') & (df.city == 'New York')).select('customer_id', 'customer_name')
"""
        res = runner.run_solution("SPK-001", correct_code, "Interview")
        if res["status"] != "PASS":
            print("RUNNER RESULTS DETAIL:", json.dumps(res, indent=2))
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(len(res["results"]) > 0)
        self.assertTrue(res["results"][0]["passed"])
        
        # 4. Test Incorrect Solution
        incorrect_code = """def solve(spark, inputs):
    df = inputs['df1']
    return df.select('customer_id', 'customer_name') # No filtering
"""
        res2 = runner.run_solution("SPK-001", incorrect_code, "Interview")
        self.assertEqual(res2["status"], "FAIL")
        self.assertFalse(res2["results"][0]["passed"])
        
        # Cleanup temp excel
        os.remove(temp_excel)

if __name__ == "__main__":
    unittest.main()
