from django.test import TestCase, Client
from django.urls import reverse
from practice.models import Problem, TestCase as DBTestCase, Dataset, SparkProfile, Goal, DailyActivity, UserRoadmap, Submission
import json
import datetime

class SparkPracticeHubTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Create a dummy problem
        self.problem = Problem.objects.create(
            id="SPK-TEST-001",
            title="Test Filter Problem",
            difficulty="Easy",
            category="Filtering & Sorting",
            description="Filter input transactions to keep only positive amounts.",
            concepts="filter",
            hints="Use df.filter(df.amount > 0)",
            comparison_mode="Exact"
        )
        
        # 2. Create datasets
        self.input_ds = Dataset.objects.create(
            name="SPK-TEST-001_df1_tc1",
            type="JSON",
            file_path="datasets/SPK-TEST-001_df1_tc1.json"
        )
        
        self.expected_ds = Dataset.objects.create(
            name="SPK-TEST-001_expected_tc1",
            type="JSON",
            file_path="datasets/SPK-TEST-001_expected_tc1.json"
        )
        
        # Create dataset files on disk for test runner
        os_makedirs = False
        import os
        os.makedirs("datasets", exist_ok=True)
        with open(self.input_ds.file_path, "w") as f:
            json.dump([
                {"transaction_id": 1, "amount": -10},
                {"transaction_id": 2, "amount": 20}
            ], f)
            
        with open(self.expected_ds.file_path, "w") as f:
            json.dump([
                {"transaction_id": 2, "amount": 20}
            ], f)
            
        # 3. Create TestCase
        self.testcase = DBTestCase.objects.create(
            problem=self.problem,
            input_datasets={"df1": "SPK-TEST-001_df1_tc1"},
            expected_output_dataset="SPK-TEST-001_expected_tc1",
            comparison_mode="Exact"
        )
        
        # 4. Create default SparkProfile
        self.profile = SparkProfile.objects.create(
            name="Interview",
            master="local[1]",
            driver_memory="512m",
            executor_memory="512m",
            executor_cores=1,
            shuffle_partitions=1,
            adaptive_query_execution=True
        )

    def tearDown(self):
        import os
        for ds in [self.input_ds, self.expected_ds]:
            if os.path.exists(ds.file_path):
                os.remove(ds.file_path)

    def test_problems_api(self):
        url = reverse('problem-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)
        # Check problem ID
        self.assertEqual(data[0]['id'], "SPK-TEST-001")

    def test_problem_details_api(self):
        url = reverse('problem-details', args=[self.problem.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['problem']['id'], "SPK-TEST-001")
        self.assertIn("df1", data['inputs_preview'])
        self.assertEqual(len(data['inputs_preview']["df1"]), 2)

    def test_dashboard_api(self):
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['problems_solved'], 0)
        self.assertEqual(data['total_problems'], 1)

    def test_profiles_api(self):
        url = reverse('profile-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_roadmaps_api(self):
        url = reverse('roadmaps')
        # GET roadmaps list
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # POST roadmap opt-in
        post_data = {"level": "Beginner", "opted_in": True}
        response = self.client.post(url, json.dumps(post_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['opted_in'], True)

    def test_pyspark_runner_correct_solution(self):
        correct_code = """def solve(spark, inputs):
    df = inputs['df1']
    return df.filter(df.amount > 0)
"""
        from practice.runner import run_solution
        res = run_solution(self.problem.id, correct_code, "Interview")
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(res["results"][0]["passed"])
        
        # Verify submission was saved
        submissions_count = Submission.objects.filter(problem=self.problem).count()
        self.assertEqual(submissions_count, 1)

    def test_pyspark_runner_incorrect_solution(self):
        incorrect_code = """def solve(spark, inputs):
    df = inputs['df1']
    return df # Return without filtering
"""
        from practice.runner import run_solution
        res = run_solution(self.problem.id, incorrect_code, "Interview")
        self.assertEqual(res["status"], "FAIL")
        self.assertFalse(res["results"][0]["passed"])
