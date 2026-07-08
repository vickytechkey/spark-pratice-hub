from rest_framework import serializers
from practice.models import Problem, TestCase, Dataset, Submission, SparkProfile, Goal, DailyActivity, UserRoadmap

class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = '__all__'

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = '__all__'

class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dataset
        fields = '__all__'

class SubmissionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_difficulty = serializers.CharField(source='problem.difficulty', read_only=True)
    
    class Meta:
        model = Submission
        fields = '__all__'

class SparkProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparkProfile
        fields = '__all__'

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = '__all__'

class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = '__all__'

class UserRoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoadmap
        fields = '__all__'
