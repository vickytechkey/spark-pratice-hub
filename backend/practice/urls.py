from django.urls import path, include
from rest_framework.routers import DefaultRouter
from practice.views import (
    DashboardView, ProblemViewSet, PracticeRunView, SparkProfileViewSet, 
    GoalViewSet, UserRoadmapViewSet, AdminImportView, SubmissionHistoryView,
    ExportSubmissionsView, ChallengeViewSet, AchievementsView, CompanyViewSet
)

router = DefaultRouter()
router.register(r'problems', ProblemViewSet, basename='problem')
router.register(r'profiles', SparkProfileViewSet, basename='profile')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'challenges', ChallengeViewSet, basename='challenge')
router.register(r'companies', CompanyViewSet, basename='company')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('practice/run/', PracticeRunView.as_view(), name='practice-run'),
    path('roadmaps/', UserRoadmapViewSet.as_view(), name='roadmaps'),
    path('achievements/', AchievementsView.as_view(), name='achievements'),
    path('admin/import/', AdminImportView.as_view(), name='admin-import'),
    path('submissions/', SubmissionHistoryView.as_view(), name='submissions-history'),
    path('export/', ExportSubmissionsView.as_view(), name='export-submissions'),
]
