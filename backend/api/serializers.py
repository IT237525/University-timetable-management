from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Batch, Subject, StaffAssignment, Availability, 
    Timetable, Comment, Room, AdminNotification, AuditLog
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone', 'is_active', 'email_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        if 'password' in attrs and 'confirm_password' in attrs:
            if attrs['password'] != attrs['confirm_password']:
                raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'phone'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class BatchSerializer(serializers.ModelSerializer):
    """Serializer for Batch model"""
    class Meta:
        model = Batch
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model"""
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    
    class Meta:
        model = Subject
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class StaffAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for StaffAssignment model"""
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    
    class Meta:
        model = StaffAssignment
        fields = '__all__'
        read_only_fields = ['id', 'assigned_date']


class AvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for Availability model"""
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    
    class Meta:
        model = Availability
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class RoomSerializer(serializers.ModelSerializer):
    """Serializer for Room model"""
    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TimetableSerializer(serializers.ModelSerializer):
    """Serializer for Timetable model"""
    batch_name = serializers.CharField(source='batch.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = Timetable
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    timetable_info = serializers.CharField(source='timetable', read_only=True)
    
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminNotificationSerializer(serializers.ModelSerializer):
    """Serializer for AdminNotification model"""
    class Meta:
        model = AdminNotification
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp']


# Nested serializers for detailed views
class BatchDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Batch with related subjects"""
    subjects = SubjectSerializer(many=True, read_only=True)
    
    class Meta:
        model = Batch
        fields = '__all__'


class SubjectDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Subject with related staff assignments"""
    staff_assignments = StaffAssignmentSerializer(many=True, read_only=True)
    batch = BatchSerializer(read_only=True)
    
    class Meta:
        model = Subject
        fields = '__all__'


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for User with related data"""
    staff_assignments = StaffAssignmentSerializer(many=True, read_only=True)
    availability = AvailabilitySerializer(many=True, read_only=True)
    teaching_schedule = TimetableSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone', 'is_active', 'email_verified', 'created_at', 'updated_at',
            'staff_assignments', 'availability', 'teaching_schedule', 'comments'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TimetableDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Timetable with all related information"""
    batch = BatchSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    staff = UserSerializer(read_only=True)
    room = RoomSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Timetable
        fields = '__all__'
