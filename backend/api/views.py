from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import (
    User, Batch, Subject, StaffAssignment, Availability, 
    Timetable, Comment, Room, AdminNotification, AuditLog
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    BatchSerializer, SubjectSerializer, StaffAssignmentSerializer,
    AvailabilitySerializer, TimetableSerializer, CommentSerializer,
    RoomSerializer, AdminNotificationSerializer, AuditLogSerializer,
    BatchDetailSerializer, SubjectDetailSerializer, UserDetailSerializer,
    TimetableDetailSerializer
)


class HealthCheckView(APIView):
    """Health check endpoint for the API"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'ok',
            'service': 'northern_uni_api',
            'version': '1.0.0'
        })


class AuthViewSet(viewsets.ViewSet):
    """Authentication views for user registration and login"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """User registration endpoint"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user_id': user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """User login endpoint"""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """User logout endpoint"""
        logout(request)
        return Response({'message': 'Logout successful'})


class UserViewSet(viewsets.ModelViewSet):
    """User management views"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user role"""
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        elif user.is_staff_member:
            return User.objects.filter(role__in=['student', 'staff'])
        else:
            return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BatchViewSet(viewsets.ModelViewSet):
    """Batch management views"""
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions"""
        if self.action == 'retrieve':
            return BatchDetailSerializer
        return BatchSerializer
    
    def get_queryset(self):
        """Filter active batches"""
        return Batch.objects.filter(is_active=True)
    
    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """Get all subjects for a specific batch"""
        batch = self.get_object()
        subjects = Subject.objects.filter(batch=batch)
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def timetable(self, request, pk=None):
        """Get timetable for a specific batch"""
        batch = self.get_object()
        timetables = Timetable.objects.filter(batch=batch).order_by('day_of_week', 'start_time')
        serializer = TimetableSerializer(timetables, many=True)
        return Response(serializer.data)


class SubjectViewSet(viewsets.ModelViewSet):
    """Subject management views"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions"""
        if self.action == 'retrieve':
            return SubjectDetailSerializer
        return SubjectSerializer
    
    @action(detail=True, methods=['get'])
    def staff(self, request, pk=None):
        """Get all staff assigned to a specific subject"""
        subject = self.get_object()
        assignments = StaffAssignment.objects.filter(subject=subject, is_active=True)
        serializer = StaffAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class StaffAssignmentViewSet(viewsets.ModelViewSet):
    """Staff assignment management views"""
    queryset = StaffAssignment.objects.all()
    serializer_class = StaffAssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter active assignments"""
        return StaffAssignment.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get assignments for a specific staff member"""
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            assignments = StaffAssignment.objects.filter(staff_id=staff_id, is_active=True)
            serializer = StaffAssignmentSerializer(assignments, many=True)
            return Response(serializer.data)
        return Response({'error': 'staff_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


class AvailabilityViewSet(viewsets.ModelViewSet):
    """Staff availability management views"""
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by staff if specified"""
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            return Availability.objects.filter(staff_id=staff_id)
        return Availability.objects.all()
    
    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get availability for a specific staff member"""
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            availability = Availability.objects.filter(staff_id=staff_id)
            serializer = AvailabilitySerializer(availability, many=True)
            return Response(serializer.data)
        return Response({'error': 'staff_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)


class RoomViewSet(viewsets.ModelViewSet):
    """Room management views"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter active rooms"""
        return Room.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available rooms for a specific time slot"""
        day = request.query_params.get('day')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        
        if day and start_time and end_time:
            # Find rooms that are not occupied during the specified time
            occupied_rooms = Timetable.objects.filter(
                day_of_week=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).values_list('room_id', flat=True)
            
            available_rooms = Room.objects.filter(is_active=True).exclude(id__in=occupied_rooms)
            serializer = RoomSerializer(available_rooms, many=True)
            return Response(serializer.data)
        
        return Response({'error': 'day, start_time, and end_time parameters required'}, 
                       status=status.HTTP_400_BAD_REQUEST)


class TimetableViewSet(viewsets.ModelViewSet):
    """Timetable management views"""
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve actions"""
        if self.action == 'retrieve':
            return TimetableDetailSerializer
        return TimetableSerializer
    
    @action(detail=False, methods=['get'])
    def by_batch(self, request):
        """Get timetables for a specific batch"""
        batch_id = request.query_params.get('batch_id')
        if batch_id:
            timetables = Timetable.objects.filter(batch_id=batch_id).order_by('day_of_week', 'start_time')
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
        return Response({'error': 'batch_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_staff(self, request):
        """Get timetables for a specific staff member"""
        staff_id = request.query_params.get('staff_id')
        if staff_id:
            timetables = Timetable.objects.filter(staff_id=staff_id).order_by('day_of_week', 'start_time')
            serializer = TimetableSerializer(timetables, many=True)
            return Response(serializer.data)
        return Response({'error': 'staff_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Check for scheduling conflicts"""
        batch_id = request.query_params.get('batch_id')
        if not batch_id:
            return Response({'error': 'batch_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        from .services.scheduling_service import ConflictResolutionService
        conflicts = ConflictResolutionService.detect_conflicts(batch_id)
        return Response({'batch_id': batch_id, 'conflicts': conflicts, 'total_conflicts': len(conflicts)})


class CommentViewSet(viewsets.ModelViewSet):
    """Comment management views"""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter approved comments for non-admin users"""
        user = self.request.user
        if user.is_admin:
            return Comment.objects.all()
        else:
            return Comment.objects.filter(is_approved=True)
    
    @action(detail=False, methods=['get'])
    def by_timetable(self, request):
        """Get comments for a specific timetable"""
        timetable_id = request.query_params.get('timetable_id')
        if timetable_id:
            comments = Comment.objects.filter(timetable_id=timetable_id, is_approved=True)
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)
        return Response({'error': 'timetable_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a comment (admin only)"""
        comment = self.get_object()
        comment.is_approved = True
        comment.save()
        return Response({'message': 'Comment approved successfully'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a comment (admin only)"""
        comment = self.get_object()
        comment.is_approved = False
        comment.save()
        return Response({'message': 'Comment rejected successfully'})

    def create(self, request, *args, **kwargs):
        """Create a new comment and notify admins for approval."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        # ensure unapproved by default unless explicitly approved
        if instance.is_approved is None or instance.is_approved is True:
            instance.is_approved = False
            instance.save(update_fields=['is_approved'])

        # create admin notification
        AdminNotification.objects.create(
            type='new_comment',
            reference_id=instance.id,
            message=f'New comment awaiting approval on timetable {instance.timetable_id}: {instance.text[:100]}'
        )

        # optional email to admins
        try:
            from .models import User
            from .utils.notifications import send_email_notification
            admin_emails = list(User.objects.filter(role='admin', is_active=True).values_list('email', flat=True))
            if admin_emails:
                send_email_notification(
                    subject='New comment pending approval',
                    message=f'User {instance.user.get_full_name()} commented on timetable {instance.timetable_id}:\n\n{instance.text}',
                    recipient_list=admin_emails
                )
        except Exception:
            # best-effort email; ignore failures
            pass

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AdminNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin notification views (read-only for now)"""
    queryset = AdminNotification.objects.all()
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit log views (read-only)"""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        """Filter by table if specified"""
        table_name = self.request.query_params.get('table')
        if table_name:
            return AuditLog.objects.filter(table_name=table_name)
        return AuditLog.objects.all()
