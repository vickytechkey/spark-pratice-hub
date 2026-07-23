from django.db import models

class Problem(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20)
    category = models.CharField(max_length=100)
    description = models.TextField()
    concepts = models.CharField(max_length=500, blank=True, null=True)
    hints = models.TextField(blank=True, null=True)
    comparison_mode = models.CharField(max_length=50, default='Exact')
    companies = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.title}"

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='testcases')
    input_datasets = models.JSONField()  # maps input_name to dataset_name
    expected_output_dataset = models.CharField(max_length=100)
    comparison_mode = models.CharField(max_length=50, blank=True, null=True)

class Dataset(models.Model):
    name = models.CharField(max_length=100, primary_key=True)
    type = models.CharField(max_length=20)  # CSV, Parquet, JSON, Excel
    file_path = models.CharField(max_length=500)

class Submission(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    code = models.TextField()
    status = models.CharField(max_length=20)  # PASS, FAIL, ERROR
    execution_time_ms = models.IntegerField(blank=True, null=True)
    metrics = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class SparkProfile(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    master = models.CharField(max_length=100, default='local[*]')
    driver_memory = models.CharField(max_length=20, default='1g')
    executor_memory = models.CharField(max_length=20, default='1g')
    executor_cores = models.IntegerField(default=1)
    shuffle_partitions = models.IntegerField(default=2)
    adaptive_query_execution = models.BooleanField(default=True)
    broadcast_threshold = models.IntegerField(default=10485760)
    serializer = models.CharField(max_length=200, default='org.apache.spark.serializer.KryoSerializer')
    default_parallelism = models.IntegerField(default=2)
    extra_configs = models.JSONField(blank=True, null=True)

class Goal(models.Model):
    type = models.CharField(max_length=20)  # Daily, Weekly, Monthly, Streak, Custom
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    priority = models.CharField(max_length=20, default='Medium')  # Low, Medium, High
    status = models.CharField(max_length=20, default='Not Started')  # Not Started, In Progress, Completed
    target = models.IntegerField()
    progress = models.IntegerField(default=0)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)  # Target completion date
    completion_date = models.DateField(blank=True, null=True)
    time_taken = models.CharField(max_length=50, blank=True, null=True)

class DailyActivity(models.Model):
    date = models.DateField(primary_key=True)
    attempts = models.IntegerField(default=0)
    solved = models.IntegerField(default=0)

class UserRoadmap(models.Model):
    level = models.CharField(max_length=50, primary_key=True)
    opted_in = models.BooleanField(default=False)

class Challenge(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_name = models.CharField(max_length=100)
    badge_icon = models.CharField(max_length=50, default='Award')  # Lucide icon name
    problems = models.ManyToManyField(Problem, related_name='challenges')

    def __str__(self):
        return self.name

class SparkMasterTopic(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50) # Beginner, Intermediate, Master
    description = models.TextField()
    subtopics = models.JSONField(default=list)
    points = models.IntegerField(default=10)
    order = models.IntegerField()

    def __str__(self):
        return f"{self.category} - {self.title}"

class SparkMasterSchedule(models.Model):
    topic = models.ForeignKey(SparkMasterTopic, on_delete=models.CASCADE, related_name='schedules')
    scheduled_date = models.DateField()
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    focus_minutes_spent = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.scheduled_date} - {self.topic.title} - {self.completed}"

