import json
import os
import zipfile
import io
import datetime
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action

from practice.models import Problem, TestCase, Dataset, Submission, SparkProfile, Goal, DailyActivity, UserRoadmap
from practice.serializers import (
    ProblemSerializer, TestCaseSerializer, DatasetSerializer, 
    SubmissionSerializer, SparkProfileSerializer, GoalSerializer, 
    DailyActivitySerializer, UserRoadmapSerializer
)
from practice.runner import run_solution
from practice.importer import import_from_excel

class DashboardView(APIView):
    def get(self, request):
        today = datetime.date.today()
        
        # 1. Streaks
        activities = DailyActivity.objects.filter(solved__gt=0).order_by('-date')
        
        current_streak = 0
        longest_streak = 0
        
        if activities.exists():
            dates = [act.date for act in activities]
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
            
            # Longest Streak
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

        # 2. Problems stats
        total_problems = Problem.objects.count()
        submissions = Submission.objects.all()
        attempted_ids = set(submissions.values_list('problem_id', flat=True))
        solved_ids = set(submissions.filter(status='PASS').values_list('problem_id', flat=True))
        
        problems_solved = len(solved_ids)
        problems_attempted = len(attempted_ids)
        success_rate = (problems_solved / problems_attempted * 100) if problems_attempted > 0 else 0
        
        # 3. Spark Metrics
        spark_jobs_executed = sum([sub.metrics.get('jobs', 0) for sub in submissions if sub.metrics])
        
        # Coding hours estimation (10 min per submission)
        coding_hours = round((submissions.count() * 10) / 60, 1)
        
        # 4. Monthly Goal Progress
        monthly_goal = Goal.objects.filter(type='Monthly', start_date__lte=today, end_date__gte=today).first()
        monthly_goal_data = None
        if monthly_goal:
            # calculate progress: unique solved problems in this month
            solved_this_month = Submission.objects.filter(
                status='PASS', 
                timestamp__date__gte=monthly_goal.start_date, 
                timestamp__date__lte=monthly_goal.end_date
            ).values('problem').distinct().count()
            monthly_goal.progress = solved_this_month
            monthly_goal.save()
            monthly_goal_data = GoalSerializer(monthly_goal).data
            
        # 5. Today's mission
        # Find an unsolved problem as today's mission
        today_mission = None
        unsolved_problem = Problem.objects.exclude(id__in=solved_ids).first()
        if unsolved_problem:
            today_mission = ProblemSerializer(unsolved_problem).data
            
        # 6. Heatmap Data (last 365 days)
        one_year_ago = today - datetime.timedelta(days=365)
        heatmap_activities = DailyActivity.objects.filter(date__gte=one_year_ago)
        heatmap_data = {
            act.date.strftime('%Y-%m-%d'): {
                'attempts': act.attempts, 
                'solved': act.solved
            } for act in heatmap_activities
        }
        
        return Response({
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'problems_solved': problems_solved,
            'problems_attempted': problems_attempted,
            'success_rate': round(success_rate, 1),
            'coding_hours': coding_hours,
            'spark_jobs_executed': spark_jobs_executed,
            'monthly_goal': monthly_goal_data,
            'today_mission': today_mission,
            'heatmap_data': heatmap_data,
            'total_problems': total_problems
        })

class ProblemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer
    
    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search', '')
        difficulty = request.query_params.get('difficulty', 'All')
        category = request.query_params.get('category', 'All')
        status_filter = request.query_params.get('status', 'All')
        
        queryset = self.queryset
        if search:
            queryset = queryset.filter(
                Q(id__icontains=search) | 
                Q(title__icontains=search) | 
                Q(description__icontains=search) | 
                Q(concepts__icontains=search)
            )
            
        if difficulty != 'All':
            queryset = queryset.filter(difficulty=difficulty)
            
        if category != 'All':
            queryset = queryset.filter(category=category)
            
        # Solved / unsolved filter
        solved_ids = set(Submission.objects.filter(status='PASS').values_list('problem_id', flat=True))
        
        problems_list = []
        for prob in queryset:
            is_solved = prob.id in solved_ids
            if status_filter == 'Completed' and not is_solved:
                continue
            if status_filter == 'Pending' and is_solved:
                continue
                
            problems_list.append({
                'id': prob.id,
                'title': prob.title,
                'difficulty': prob.difficulty,
                'category': prob.category,
                'description': prob.description,
                'concepts': prob.concepts,
                'hints': prob.hints,
                'comparison_mode': prob.comparison_mode,
                'is_solved': is_solved
            })
            
        return Response(problems_list)

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        problem = self.get_object()
        test_cases = TestCase.objects.filter(problem=problem)
        
        # Load input dataset preview (from the first test case)
        inputs_preview = {}
        if test_cases.exists():
            tc = test_cases.first()
            for key, ds_name in tc.input_datasets.items():
                dataset = Dataset.objects.filter(name=ds_name).first()
                if dataset and os.path.exists(dataset.file_path):
                    try:
                        with open(dataset.file_path, 'r') as f:
                            data = json.load(f)
                            inputs_preview[key] = data[:10]  # first 10 rows
                    except Exception:
                        pass
                        
        # Load expected output preview (from first test case)
        expected_preview = []
        if test_cases.exists():
            tc = test_cases.first()
            expected_ds = Dataset.objects.filter(name=tc.expected_output_dataset).first()
            if expected_ds and os.path.exists(expected_ds.file_path):
                try:
                    with open(expected_ds.file_path, 'r') as f:
                        data = json.load(f)
                        expected_preview = data[:10]
                except Exception:
                    pass
                    
        return Response({
            'problem': ProblemSerializer(problem).data,
            'inputs_preview': inputs_preview,
            'expected_preview': expected_preview,
            'test_cases_count': test_cases.count()
        })

class PracticeRunView(APIView):
    def post(self, request):
        problem_id = request.data.get('problem_id')
        code = request.data.get('code')
        profile_name = request.data.get('profile_name', 'Interview')
        
        if not problem_id or not code:
            return Response({'error': 'problem_id and code are required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        res = run_solution(problem_id, code, profile_name, submit=True)
        return Response(res)

class SparkProfileViewSet(viewsets.ModelViewSet):
    queryset = SparkProfile.objects.all()
    serializer_class = SparkProfileSerializer

class GoalViewSet(viewsets.ModelViewSet):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer

class UserRoadmapViewSet(APIView):
    def get(self, request):
        levels = ["Beginner", "Intermediate", "Advanced", "Expert", "Master"]
        roadmaps = []
        for lvl in levels:
            rm, created = UserRoadmap.objects.get_or_create(level=lvl, defaults={'opted_in': False})
            roadmaps.append(UserRoadmapSerializer(rm).data)
        return Response(roadmaps)
        
    def post(self, request):
        level = request.data.get('level')
        opted_in = request.data.get('opted_in', False)
        if not level:
            return Response({'error': 'level is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        rm = UserRoadmap.objects.filter(level=level).first()
        if rm:
            rm.opted_in = opted_in
            rm.save()
            return Response(UserRoadmapSerializer(rm).data)
        return Response({'error': 'Level not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminImportView(APIView):
    def post(self, request):
        excel_file = request.FILES.get('file')
        if not excel_file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Write to temporary file
        temp_path = f"uploads/{excel_file.name}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, 'wb+') as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)
                
        success, msg = import_from_excel(temp_path)
        try:
            os.remove(temp_path)
        except Exception:
            pass
            
        if success:
            return Response({'message': msg})
        else:
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

class SubmissionHistoryView(APIView):
    def get(self, request):
        submissions = Submission.objects.all().order_by('-timestamp')
        return Response(SubmissionSerializer(submissions, many=True).data)

class ExportSubmissionsView(APIView):
    def get(self, request):
        export_format = request.query_params.get('format', 'csv')
        submissions = Submission.objects.all().order_by('-timestamp')
        
        if export_format == 'csv':
            import csv
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="submission_history.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Problem ID', 'Problem Title', 'Status', 'Runtime (ms)', 'Timestamp'])
            for sub in submissions:
                writer.writerow([
                    sub.id, 
                    sub.problem.id, 
                    sub.problem.title, 
                    sub.status, 
                    sub.execution_time_ms, 
                    sub.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                ])
            return response
            
        elif export_format == 'excel':
            import pandas as pd
            data = []
            for sub in submissions:
                data.append({
                    'ID': sub.id,
                    'Problem ID': sub.problem.id,
                    'Problem Title': sub.problem.title,
                    'Status': sub.status,
                    'Runtime (ms)': sub.execution_time_ms,
                    'Timestamp': sub.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                })
            df = pd.DataFrame(data)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Submissions')
            
            output.seek(0)
            response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="submission_history.xlsx"'
            return response
            
        elif export_format == 'zip':
            # Export user's codes as code files in a zip
            byte_stream = io.BytesIO()
            with zipfile.ZipFile(byte_stream, 'w') as zip_file:
                for sub in submissions:
                    filename = f"submissions/sub_{sub.id}_{sub.problem.id}_{sub.status}.py"
                    zip_file.writestr(filename, sub.code)
                    
            byte_stream.seek(0)
            response = FileResponse(byte_stream, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="submissions.zip"'
            return response
            
        return Response({'error': 'Invalid format'}, status=status.HTTP_400_BAD_REQUEST)
