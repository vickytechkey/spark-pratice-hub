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

from practice.models import Problem, TestCase, Dataset, Submission, SparkProfile, Goal, DailyActivity, UserRoadmap, Challenge
from practice.serializers import (
    ProblemSerializer, TestCaseSerializer, DatasetSerializer, 
    SubmissionSerializer, SparkProfileSerializer, GoalSerializer, 
    DailyActivitySerializer, UserRoadmapSerializer, ChallengeSerializer
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
        
        # 4. Active & Custom Goals progress update
        active_goals = Goal.objects.exclude(status='Completed')
        for goal in active_goals:
            if goal.type in ['Monthly', 'Daily', 'Weekly']:
                start = goal.start_date or (today - datetime.timedelta(days=30))
                end = goal.end_date or today
                solved_count = Submission.objects.filter(
                    status='PASS', 
                    timestamp__date__gte=start, 
                    timestamp__date__lte=end
                ).values('problem').distinct().count()
                goal.progress = solved_count
            elif goal.type == 'Custom':
                if goal.category:
                    q = Submission.objects.filter(status='PASS', problem__category=goal.category)
                    if goal.start_date:
                        q = q.filter(timestamp__date__gte=goal.start_date)
                    if goal.end_date:
                        q = q.filter(timestamp__date__lte=goal.end_date)
                    solved_count = q.values('problem').distinct().count()
                else:
                    q = Submission.objects.filter(status='PASS')
                    if goal.start_date:
                        q = q.filter(timestamp__date__gte=goal.start_date)
                    if goal.end_date:
                        q = q.filter(timestamp__date__lte=goal.end_date)
                    solved_count = q.values('problem').distinct().count()
                goal.progress = solved_count

            # Auto-completion trigger
            if goal.progress >= goal.target:
                goal.status = 'Completed'
                goal.completion_date = today
                if goal.start_date:
                    days_taken = (today - goal.start_date).days
                    goal.time_taken = f"{days_taken} days" if days_taken > 0 else "Less than 1 day"
                else:
                    goal.time_taken = "1 day"
            elif goal.progress > 0:
                goal.status = 'In Progress'
            else:
                goal.status = 'Not Started'
            goal.save()

        active_goals_qs = Goal.objects.exclude(status='Completed')
        active_goals_data = GoalSerializer(active_goals_qs, many=True).data

        # Keep legacy monthly_goal key for compatibility
        monthly_goal = Goal.objects.filter(type='Monthly').exclude(status='Completed').first()
        monthly_goal_data = GoalSerializer(monthly_goal).data if monthly_goal else None
            
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
            'active_goals': active_goals_data,
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
        submit = request.data.get('submit', True)
        
        if not problem_id or not code:
            return Response({'error': 'problem_id and code are required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        res = run_solution(problem_id, code, profile_name, submit=submit)
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
        solved_ids = set(Submission.objects.filter(status='PASS').values_list('problem_id', flat=True))
        
        level_categories = {
            "Beginner": ["Filtering & Sorting", "Date & String"],
            "Intermediate": ["Aggregations", "Joins"],
            "Advanced": ["Advanced Nested & Pivot", "Window Functions"],
            "Expert": ["Data Cleaning & Null Handling", "Array & Map Operations"],
            "Master": ["Performance & Optimization", "User Defined Functions (UDFs)", "User Defined Functions (UDFs)"]
        }
        
        level_skills = {
            "Beginner": ["DataFrame Creation", "Filtering", "Sorting", "Basic Select", "String manipulation"],
            "Intermediate": ["Aggregations", "Group By", "Inner/Outer Joins", "Column operations"],
            "Advanced": ["Window Functions", "Analytical Partitioning", "Pivoting", "Nested Structs", "Array explosion"],
            "Expert": ["Custom UDFs", "Regex extraction", "Null filling (fillna/coalesce)", "Data Cleaning"],
            "Master": ["Performance Tuning", "Query Optimization", "Repartitioning", "Coalescing", "Broadcast joins"]
        }
        
        level_multipliers = {
            "Beginner": 15,
            "Intermediate": 25,
            "Advanced": 35,
            "Expert": 50,
            "Master": 60
        }
        
        roadmaps = []
        for lvl in levels:
            rm, created = UserRoadmap.objects.get_or_create(level=lvl, defaults={'opted_in': False})
            cats = level_categories.get(lvl, [])
            
            probs_qs = Problem.objects.filter(category__in=cats)
            total_count = probs_qs.count()
            
            completed_probs = [p for p in probs_qs if p.id in solved_ids]
            completed_count = len(completed_probs)
            percentage = round((completed_count / total_count * 100), 1) if total_count > 0 else 0
            
            multiplier = level_multipliers.get(lvl, 20)
            remaining_count = total_count - completed_count
            est_time_minutes = remaining_count * multiplier
            
            problems_list = []
            for p in probs_qs:
                problems_list.append({
                    'id': p.id,
                    'title': p.title,
                    'difficulty': p.difficulty,
                    'category': p.category,
                    'is_solved': p.id in solved_ids
                })
                
            roadmaps.append({
                'level': rm.level,
                'opted_in': rm.opted_in,
                'total_problems': total_count,
                'completed_problems_count': completed_count,
                'completion_percentage': percentage,
                'estimated_time_minutes': est_time_minutes,
                'skills_covered': level_skills.get(lvl, []),
                'problems': problems_list
            })
            
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

class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer

    @action(detail=False, methods=['get'])
    def status(self, request):
        solved_ids = set(Submission.objects.filter(status='PASS').values_list('problem_id', flat=True))
        challenges = Challenge.objects.all()
        res = []
        for ch in challenges:
            problems = ch.problems.all()
            completed_problems = [p.id for p in problems if p.id in solved_ids]
            total_problems = problems.count()
            percentage = round((len(completed_problems) / total_problems * 100), 1) if total_problems > 0 else 0
            is_unlocked = len(completed_problems) == total_problems if total_problems > 0 else False
            
            problems_list = []
            for p in problems:
                problems_list.append({
                    'id': p.id,
                    'title': p.title,
                    'difficulty': p.difficulty,
                    'category': p.category,
                    'is_solved': p.id in solved_ids
                })

            res.append({
                'id': ch.id,
                'name': ch.name,
                'description': ch.description,
                'badge_name': ch.badge_name,
                'badge_icon': ch.badge_icon,
                'total_problems': total_problems,
                'completed_problems_count': len(completed_problems),
                'completion_percentage': percentage,
                'is_unlocked': is_unlocked,
                'problems': problems_list
            })
        return Response(res)

class AchievementsView(APIView):
    def get(self, request):
        completed_goals = Goal.objects.filter(status='Completed').order_by('-completion_date')
        goals_data = GoalSerializer(completed_goals, many=True).data

        solved_ids = set(Submission.objects.filter(status='PASS').values_list('problem_id', flat=True))
        earned_badges = []
        challenges = Challenge.objects.all()
        for ch in challenges:
            prob_ids = [p.id for p in ch.problems.all()]
            if not prob_ids:
                continue
            is_earned = all(pid in solved_ids for pid in prob_ids)
            if is_earned:
                last_sub = Submission.objects.filter(status='PASS', problem_id__in=prob_ids).order_by('-timestamp').first()
                completion_date = last_sub.timestamp.date() if last_sub else timezone.now().date()
                
                earned_badges.append({
                    'id': ch.id,
                    'name': ch.name,
                    'description': ch.description,
                    'badge_name': ch.badge_name,
                    'badge_icon': ch.badge_icon,
                    'completion_date': completion_date,
                    'problems_count': len(prob_ids)
                })

        return Response({
            'goals': goals_data,
            'badges': earned_badges
        })

class CompanyViewSet(viewsets.ViewSet):
    def list(self, request):
        companies_list = [
            "Google", "Meta", "Amazon", "Microsoft", "Apple", "Netflix", "Uber", 
            "Airbnb", "LinkedIn", "Adobe", "Salesforce", "Databricks", "Snowflake", 
            "NVIDIA", "Oracle", "Atlassian", "Stripe", "Bloomberg", "Walmart Global Tech", 
            "Goldman Sachs", "JPMorgan Chase", "Cisco", "Intel", "Qualcomm", "PayPal", 
            "Expedia", "Booking.com", "Spotify"
        ]
        solved_ids = set(Submission.objects.filter(status='PASS').values_list('problem_id', flat=True))
        all_problems = Problem.objects.all()
        
        company_problems_map = {name: [] for name in companies_list}
        for p in all_problems:
            if p.companies:
                for c_entry in p.companies:
                    c_name = c_entry.get('company')
                    if c_name in company_problems_map:
                        company_problems_map[c_name].append(p)
                        
        res = []
        for name in companies_list:
            probs = company_problems_map[name]
            total_problems = len(probs)
            solved_probs = [p for p in probs if p.id in solved_ids]
            completed_count = len(solved_probs)
            percentage = round((completed_count / total_problems * 100), 1) if total_problems > 0 else 0
            
            easy = sum(1 for p in probs if p.difficulty == 'Easy')
            medium = sum(1 for p in probs if p.difficulty == 'Medium')
            hard = sum(1 for p in probs if p.difficulty == 'Hard')
            
            topics_dict = {}
            for p in probs:
                topics_dict[p.category] = topics_dict.get(p.category, 0) + 1
            frequent_topics = sorted(topics_dict.keys(), key=lambda t: topics_dict[t], reverse=True)[:3]

            res.append({
                'name': name,
                'total_problems': total_problems,
                'completed_problems_count': completed_count,
                'completion_percentage': percentage,
                'difficulty_distribution': {'Easy': easy, 'Medium': medium, 'Hard': hard},
                'frequent_topics': frequent_topics
            })
        return Response(res)

    def retrieve(self, request, pk=None):
        company_name = pk
        solved_ids = set(Submission.objects.filter(status='PASS').values_list('problem_id', flat=True))
        
        all_problems = Problem.objects.all()
        probs = []
        for p in all_problems:
            if p.companies:
                for c_entry in p.companies:
                    if c_entry.get('company') == company_name:
                        probs.append((p, c_entry.get('frequency', 'Occasionally Asked')))
                        break
                        
        total_problems = len(probs)
        completed_probs = [p for p, _ in probs if p.id in solved_ids]
        completed_count = len(completed_probs)
        percentage = round((completed_count / total_problems * 100), 1) if total_problems > 0 else 0
        
        easy = sum(1 for p, _ in probs if p.difficulty == 'Easy')
        medium = sum(1 for p, _ in probs if p.difficulty == 'Medium')
        hard = sum(1 for p, _ in probs if p.difficulty == 'Hard')
        
        topics_dict = {}
        for p, _ in probs:
            topics_dict[p.category] = topics_dict.get(p.category, 0) + 1
        frequent_topics = sorted(topics_dict.keys(), key=lambda t: topics_dict[t], reverse=True)[:5]
        
        problem_list = []
        for p, freq in probs:
            problem_list.append({
                'id': p.id,
                'title': p.title,
                'difficulty': p.difficulty,
                'category': p.category,
                'is_solved': p.id in solved_ids,
                'frequency': freq
            })
            
        recently_added = problem_list[-3:] if len(problem_list) >= 3 else problem_list

        return Response({
            'name': company_name,
            'total_problems': total_problems,
            'completed_problems_count': completed_count,
            'completion_percentage': percentage,
            'difficulty_distribution': {'Easy': easy, 'Medium': medium, 'Hard': hard},
            'frequent_topics': frequent_topics,
            'problems': problem_list,
            'recently_added': recently_added
        })
