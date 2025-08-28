from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    User, Batch, Subject, StaffAssignment, Availability, 
    Timetable, Comment, Room, AdminNotification, AuditLog
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin interface for User model"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'email_verified', 'created_at')
    list_filter = ('role', 'is_active', 'email_verified', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'email_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name'),
        }),
    )


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    """Admin interface for Batch model"""
    list_display = ('name', 'academic_year', 'semester', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('academic_year', 'semester', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'academic_year')
    ordering = ('academic_year', 'semester', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'academic_year', 'semester')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Time Constraints', {
            'fields': ('weekday_start_time', 'weekday_end_time', 'weekend_start_time', 'weekend_end_time')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin interface for Subject model"""
    list_display = ('code', 'name', 'batch', 'lecture_duration', 'tutorial_duration', 'lab_duration', 'total_credits', 'created_at')
    list_filter = ('batch', 'total_credits', 'created_at')
    search_fields = ('code', 'name', 'description')
    ordering = ('code', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'batch', 'total_credits')
        }),
        ('Component Durations (minutes)', {
            'fields': ('lecture_duration', 'tutorial_duration', 'lab_duration')
        }),
    )


@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for StaffAssignment model"""
    list_display = ('staff', 'subject', 'batch', 'assignment_type', 'is_active', 'assigned_date')
    list_filter = ('assignment_type', 'is_active', 'assigned_date', 'batch')
    search_fields = ('staff__username', 'staff__first_name', 'staff__last_name', 'subject__code', 'subject__name')
    ordering = ('staff', 'subject', 'batch')
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('staff', 'subject', 'batch', 'assignment_type')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """Admin interface for Availability model"""
    list_display = ('staff', 'day_of_week', 'start_time', 'end_time', 'availability_type', 'is_available', 'created_at')
    list_filter = ('day_of_week', 'availability_type', 'is_available', 'created_at')
    search_fields = ('staff__username', 'staff__first_name', 'staff__last_name')
    ordering = ('staff', 'day_of_week')
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('staff', 'availability_type')
        }),
        ('Schedule', {
            'fields': ('day_of_week', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('is_available',)
        }),
    )


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    """Admin interface for Timetable model"""
    list_display = ('batch', 'subject', 'staff', 'day_of_week', 'start_time', 'end_time', 'component_type', 'room', 'is_recurring', 'created_at')
    list_filter = ('batch', 'component_type', 'day_of_week', 'is_recurring', 'created_at')
    search_fields = ('batch__name', 'subject__code', 'subject__name', 'staff__username')
    ordering = ('batch', 'day_of_week', 'start_time')
    
    fieldsets = (
        ('Schedule Information', {
            'fields': ('batch', 'subject', 'staff', 'component_type')
        }),
        ('Time and Day', {
            'fields': ('day_of_week', 'start_time', 'end_time', 'week_number')
        }),
        ('Location and Recurrence', {
            'fields': ('room', 'is_recurring')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('batch', 'subject', 'staff', 'room')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for Comment model"""
    list_display = ('user', 'timetable', 'rating', 'is_approved', 'parent_comment', 'created_at')
    list_filter = ('is_approved', 'rating', 'created_at')
    search_fields = ('user__username', 'text', 'timetable__subject__code')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('user', 'timetable', 'parent_comment', 'text', 'rating')
        }),
        ('Moderation', {
            'fields': ('is_approved',)
        }),
    )
    
    actions = ['approve_comments', 'reject_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comments were successfully approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def reject_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comments were successfully rejected.')
    reject_comments.short_description = "Reject selected comments"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin interface for Room model"""
    list_display = ('name', 'room_type', 'capacity', 'building', 'floor', 'is_active', 'created_at')
    list_filter = ('room_type', 'building', 'floor', 'is_active', 'created_at')
    search_fields = ('name', 'building')
    ordering = ('building', 'floor', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'room_type', 'capacity')
        }),
        ('Location', {
            'fields': ('building', 'floor')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    """Admin interface for AdminNotification model"""
    list_display = ('type', 'reference_id', 'message', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('message',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('type', 'reference_id', 'message')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications were marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications were marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model"""
    list_display = ('action', 'table_name', 'record_id', 'user', 'timestamp', 'ip_address')
    list_filter = ('action', 'table_name', 'timestamp')
    search_fields = ('table_name', 'user__username', 'ip_address')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Action Details', {
            'fields': ('action', 'table_name', 'record_id')
        }),
        ('User Information', {
            'fields': ('user', 'ip_address', 'user_agent')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Customize admin site
admin.site.site_header = "University Timetable Management System"
admin.site.site_title = "Timetable Admin"
admin.site.index_title = "Welcome to Timetable Management"
