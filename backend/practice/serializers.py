from rest_framework import serializers
from practice.models import Problem, TestCase, Dataset, Submission, SparkProfile, Goal, DailyActivity, UserRoadmap, Challenge, SparkMasterTopic, SparkMasterSchedule

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
    days_remaining = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Goal
        fields = '__all__'

    def get_days_remaining(self, obj):
        if obj.end_date:
            import datetime
            delta = obj.end_date - datetime.date.today()
            return max(0, delta.days)
        return None

class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = '__all__'

class UserRoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRoadmap
        fields = '__all__'

class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = '__all__'

class SparkMasterTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparkMasterTopic
        fields = '__all__'

class SparkMasterScheduleSerializer(serializers.ModelSerializer):
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    topic_category = serializers.CharField(source='topic.category', read_only=True)
    topic_description = serializers.CharField(source='topic.description', read_only=True)
    topic_subtopics = serializers.JSONField(source='topic.subtopics', read_only=True)
    topic_points = serializers.IntegerField(source='topic.points', read_only=True)

    class Meta:
        model = SparkMasterSchedule
        fields = '__all__'

