from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views, advanced_views
from .utils import notifications  # noqa: F401 ensure module is discoverable

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'batches', views.BatchViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'staff-assignments', views.StaffAssignmentViewSet)
router.register(r'availability', views.AvailabilityViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'timetables', views.TimetableViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'admin-notifications', views.AdminNotificationViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)

# URL patterns
urlpatterns = [
    # Health check endpoint
    path('health/', views.HealthCheckView.as_view(), name='api-health'),
    
    # Authentication endpoints
    path('auth/', include([
        path('register/', auth_views.UserRegistrationView.as_view(), name='auth-register'),
        path('login/', auth_views.UserLoginView.as_view(), name='auth-login'),
        path('logout/', auth_views.LogoutView.as_view(), name='auth-logout'),
        path('profile/', auth_views.UserProfileView.as_view(), name='auth-profile'),
        path('change-password/', auth_views.ChangePasswordView.as_view(), name='auth-change-password'),
        path('refresh/', auth_views.refresh_token_view, name='auth-refresh'),
        path('activity/', auth_views.user_activity_view, name='auth-activity'),
    ])),
    
    # JWT Token endpoints
    path('token/', auth_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Advanced features
    path('scheduling/', include([
        path('generate/', advanced_views.TimetableGenerationView.as_view(), name='generate-timetable'),
        path('conflicts/', advanced_views.ConflictManagementView.as_view(), name='conflict-management'),
        path('staff/', advanced_views.StaffSchedulingView.as_view(), name='staff-scheduling'),
        path('batch/', advanced_views.BatchManagementView.as_view(), name='batch-management'),
        path('analytics/', advanced_views.AnalyticsView.as_view(), name='analytics'),
    ])),
    
    # Advanced timetable operations
    path('advanced-timetables/', include([
        path('weekly-batch/', advanced_views.AdvancedTimetableViewSet.as_view({'get': 'by_batch_weekly'}), name='weekly-batch'),
        path('weekly-staff/', advanced_views.AdvancedTimetableViewSet.as_view({'get': 'by_staff_weekly'}), name='weekly-staff'),
        path('export-pdf/', advanced_views.AdvancedTimetableViewSet.as_view({'get': 'export_pdf'}), name='export-pdf'),
        path('export-ics/', advanced_views.AdvancedTimetableViewSet.as_view({'get': 'export-ics'}), name='export-ics'),
    ])),
    
    # Include router URLs
    path('', include(router.urls)),
]
