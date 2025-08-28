from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Supports Students, Staff, and Admin roles
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_staff_member(self):
        return self.role == 'staff'
    
    @property
    def is_admin(self):
        return self.role == 'admin'


class Batch(models.Model):
    """
    Academic batches (e.g., Y1S1, Y2S2)
    """
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True, help_text="e.g., Y1S1, Y2S2")
    description = models.TextField(blank=True, null=True)
    academic_year = models.CharField(max_length=9, help_text="e.g., 2024-2025")
    semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    weekday_start_time = models.TimeField(default='08:30:00')
    weekday_end_time = models.TimeField(default='17:30:00')
    weekend_start_time = models.TimeField(default='08:30:00')
    weekend_end_time = models.TimeField(default='20:30:00')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'batches'
        verbose_name = 'Batch'
        verbose_name_plural = 'Batches'
        ordering = ['academic_year', 'semester', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.academic_year}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")


class Subject(models.Model):
    """
    Academic subjects with configurable component durations
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True, help_text="e.g., CS101, MATH201")
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='subjects')
    lecture_duration = models.IntegerField(
        default=60, 
        validators=[MinValueValidator(60), MaxValueValidator(120)],
        help_text="Duration in minutes (60-120)"
    )
    tutorial_duration = models.IntegerField(
        default=60,
        validators=[MinValueValidator(60), MaxValueValidator(120)],
        help_text="Duration in minutes (60-120)"
    )
    lab_duration = models.IntegerField(
        default=120,
        validators=[MinValueValidator(60), MaxValueValidator(120)],
        help_text="Duration in minutes (60-120)"
    )
    total_credits = models.IntegerField(default=3)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'subjects'
        verbose_name = 'Subject'
        verbose_name_plural = 'Subjects'
        ordering = ['code', 'name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_total_hours(self):
        """Calculate total teaching hours for the subject"""
        return (self.lecture_duration + self.tutorial_duration + self.lab_duration) / 60


class StaffAssignment(models.Model):
    """
    Assignment of staff members to subjects for specific batches
    """
    ASSIGNMENT_TYPE_CHOICES = [
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('assistant', 'Assistant'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='staff_assignments')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='staff_assignments')
    assignment_type = models.CharField(
        max_length=10, 
        choices=ASSIGNMENT_TYPE_CHOICES, 
        default='primary'
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'staff_assignments'
        verbose_name = 'Staff Assignment'
        verbose_name_plural = 'Staff Assignments'
        unique_together = ['staff', 'subject', 'batch']
        ordering = ['staff', 'subject', 'batch']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.subject.code} ({self.batch.name})"


class Availability(models.Model):
    """
    Staff availability for teaching assignments
    """
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    AVAILABILITY_TYPE_CHOICES = [
        ('weekday', 'Weekday'),
        ('weekend', 'Weekend'),
        ('both', 'Both'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    availability_type = models.CharField(max_length=10, choices=AVAILABILITY_TYPE_CHOICES)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'availability'
        verbose_name = 'Availability'
        verbose_name_plural = 'Availability'
        unique_together = ['staff', 'day_of_week']
        ordering = ['staff', 'day_of_week']
    
    def __str__(self):
        return f"{self.staff.get_full_name()} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")


class Timetable(models.Model):
    """
    Generated timetables for batches
    """
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    COMPONENT_TYPE_CHOICES = [
        ('lecture', 'Lecture'),
        ('tutorial', 'Tutorial'),
        ('lab', 'Lab'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='timetables')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetables')
    staff = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_schedule')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    component_type = models.CharField(max_length=10, choices=COMPONENT_TYPE_CHOICES)
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True, related_name='timetables')
    week_number = models.IntegerField(default=1, help_text="Week number for recurring schedules")
    is_recurring = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'timetables'
        verbose_name = 'Timetable'
        verbose_name_plural = 'Timetables'
        ordering = ['batch', 'day_of_week', 'start_time']
        unique_together = ['batch', 'day_of_week', 'start_time', 'component_type']
    
    def __str__(self):
        return f"{self.batch.name} - {self.subject.code} ({self.get_component_type_display()}) - {self.get_day_of_week_display()}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes"""
        start = self.start_time
        end = self.end_time
        return (end.hour - start.hour) * 60 + (end.minute - start.minute)


class Comment(models.Model):
    """
    Student feedback and comments on timetables
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    text = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, 
        blank=True,
        help_text="Rating from 1 to 5"
    )
    is_approved = models.BooleanField(default=False, help_text="Admin approval for visibility")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.get_full_name()} on {self.timetable}"
    
    @property
    def is_reply(self):
        return self.parent_comment is not None


class Room(models.Model):
    """
    Classroom and laboratory rooms
    """
    ROOM_TYPE_CHOICES = [
        ('classroom', 'Classroom'),
        ('laboratory', 'Laboratory'),
        ('lecture_hall', 'Lecture Hall'),
        ('tutorial_room', 'Tutorial Room'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='classroom')
    capacity = models.IntegerField(help_text="Maximum number of students")
    building = models.CharField(max_length=100, blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rooms'
        verbose_name = 'Room'
        verbose_name_plural = 'Rooms'
        ordering = ['building', 'floor', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()}) - Capacity: {self.capacity}"


class AdminNotification(models.Model):
    """
    Notifications for administrators
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('new_comment', 'New Comment'),
        ('timetable_conflict', 'Timetable Conflict'),
        ('system_alert', 'System Alert'),
        ('user_request', 'User Request'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    reference_id = models.BigIntegerField(help_text="ID of the referenced object")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_notifications'
        verbose_name = 'Admin Notification'
        verbose_name_plural = 'Admin Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.message[:50]}..."


class AuditLog(models.Model):
    """
    Audit trail for system changes
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    table_name = models.CharField(max_length=100)
    record_id = models.BigIntegerField()
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} on {self.table_name}:{self.record_id} by {self.user}"
