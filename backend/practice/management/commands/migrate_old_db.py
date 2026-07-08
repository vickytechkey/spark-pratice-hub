import os
import json
import sqlite3
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from practice.models import Problem, TestCase, Dataset, Submission, SparkProfile, Goal, DailyActivity, UserRoadmap

class Command(BaseCommand):
    help = 'Migrate data from old SQLite tables to Django native tables'

    def handle(self, *args, **kwargs):
        db_path = settings.DATABASES['default']['NAME']
        self.stdout.write(f"Connecting to database at: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Helper to check table existence
        def table_exists(table_name):
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            return cursor.fetchone() is not None

        # 1. Migrate Problems
        if table_exists('problems'):
            self.stdout.write("Migrating problems...")
            cursor.execute("SELECT * FROM problems")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                for row in rows:
                    row_dict = dict(row)
                    Problem.objects.update_or_create(
                        id=row_dict['id'],
                        defaults={
                            'title': row_dict['title'],
                            'difficulty': row_dict['difficulty'],
                            'category': row_dict['category'],
                            'description': row_dict['description'],
                            'concepts': row_dict.get('concepts'),
                            'hints': row_dict.get('hints'),
                            'comparison_mode': row_dict.get('comparison_mode', 'Exact')
                        }
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} problems."))

        # 2. Migrate Datasets
        if table_exists('datasets'):
            self.stdout.write("Migrating datasets...")
            cursor.execute("SELECT * FROM datasets")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                for row in rows:
                    row_dict = dict(row)
                    Dataset.objects.update_or_create(
                        name=row_dict['name'],
                        defaults={
                            'type': row_dict['type'],
                            'file_path': row_dict['file_path']
                        }
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} datasets."))

        # 3. Migrate Test Cases
        if table_exists('test_cases'):
            self.stdout.write("Migrating test cases...")
            cursor.execute("SELECT * FROM test_cases")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                TestCase.objects.all().delete()
                for row in rows:
                    row_dict = dict(row)
                    try:
                        prob = Problem.objects.get(id=row_dict['problem_id'])
                        input_ds = row_dict['input_datasets']
                        if isinstance(input_ds, str):
                            input_ds = json.loads(input_ds)
                            
                        TestCase.objects.create(
                            problem=prob,
                            input_datasets=input_ds,
                            expected_output_dataset=row_dict['expected_output_dataset'],
                            comparison_mode=row_dict.get('comparison_mode')
                        )
                        count += 1
                    except Problem.DoesNotExist:
                        pass
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} test cases."))

        # 4. Migrate Spark Profiles
        if table_exists('spark_profiles'):
            self.stdout.write("Migrating spark profiles...")
            cursor.execute("SELECT * FROM spark_profiles")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                for row in rows:
                    row_dict = dict(row)
                    
                    extra = row_dict.get('extra_configs')
                    if extra and isinstance(extra, str):
                        try:
                            extra = json.loads(extra)
                        except Exception:
                            extra = None
                    
                    SparkProfile.objects.update_or_create(
                        name=row_dict['name'],
                        defaults={
                            'master': row_dict['master'],
                            'driver_memory': row_dict['driver_memory'],
                            'executor_memory': row_dict['executor_memory'],
                            'executor_cores': row_dict['executor_cores'],
                            'shuffle_partitions': row_dict['shuffle_partitions'],
                            'adaptive_query_execution': bool(row_dict.get('adaptive_query_execution', 1)),
                            'broadcast_threshold': row_dict.get('broadcast_threshold', 10485760),
                            'serializer': row_dict.get('serializer', 'org.apache.spark.serializer.KryoSerializer'),
                            'default_parallelism': row_dict.get('default_parallelism', 2),
                            'extra_configs': extra
                        }
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} spark profiles."))

        # 5. Migrate Goals
        if table_exists('goals'):
            self.stdout.write("Migrating goals...")
            cursor.execute("SELECT * FROM goals")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                Goal.objects.all().delete()
                for row in rows:
                    row_dict = dict(row)
                    try:
                        s_date = datetime.datetime.strptime(row_dict['start_date'], "%Y-%m-%d").date()
                        e_date = datetime.datetime.strptime(row_dict['end_date'], "%Y-%m-%d").date()
                    except Exception:
                        s_date = datetime.date.today()
                        e_date = datetime.date.today()
                        
                    Goal.objects.create(
                        type=row_dict['type'],
                        target=row_dict['target'],
                        progress=row_dict.get('progress', 0),
                        start_date=s_date,
                        end_date=e_date
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} goals."))

        # 6. Migrate Daily Activity
        if table_exists('daily_activity'):
            self.stdout.write("Migrating daily activity...")
            cursor.execute("SELECT * FROM daily_activity")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                for row in rows:
                    row_dict = dict(row)
                    try:
                        act_date = datetime.datetime.strptime(row_dict['date'], "%Y-%m-%d").date()
                    except Exception:
                        continue
                    DailyActivity.objects.update_or_create(
                        date=act_date,
                        defaults={
                            'attempts': row_dict.get('attempts', 0),
                            'solved': row_dict.get('solved', 0)
                        }
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} daily activity records."))

        # 7. Migrate User Roadmaps
        if table_exists('user_roadmaps'):
            self.stdout.write("Migrating user roadmaps...")
            cursor.execute("SELECT * FROM user_roadmaps")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                for row in rows:
                    row_dict = dict(row)
                    UserRoadmap.objects.update_or_create(
                        level=row_dict['level'],
                        defaults={
                            'opted_in': bool(row_dict.get('opted_in', 0))
                        }
                    )
                    count += 1
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} user roadmaps."))

        # 8. Migrate Submissions
        if table_exists('submissions'):
            self.stdout.write("Migrating submissions...")
            cursor.execute("SELECT * FROM submissions")
            rows = cursor.fetchall()
            count = 0
            with transaction.atomic():
                Submission.objects.all().delete()
                for row in rows:
                    row_dict = dict(row)
                    try:
                        prob = Problem.objects.get(id=row_dict['problem_id'])
                        
                        metrics = row_dict.get('metrics')
                        if metrics and isinstance(metrics, str):
                            try:
                                metrics = json.loads(metrics)
                            except Exception:
                                metrics = None
                                
                        try:
                            timestamp = datetime.datetime.strptime(row_dict['timestamp'], "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            timestamp = datetime.datetime.now()
                            
                        Submission.objects.create(
                            problem=prob,
                            code=row_dict['code'],
                            status=row_dict['status'],
                            execution_time_ms=row_dict.get('execution_time_ms'),
                            metrics=metrics,
                            error_message=row_dict.get('error_message'),
                            timestamp=timestamp
                        )
                        count += 1
                    except Problem.DoesNotExist:
                        pass
            self.stdout.write(self.style.SUCCESS(f"Migrated {count} submissions."))

        conn.close()
        self.stdout.write(self.style.SUCCESS("All data migrated to Django tables in atomic transactions!"))
