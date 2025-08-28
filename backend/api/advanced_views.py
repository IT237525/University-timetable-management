"""
Advanced API Views for Timetable Management System
Includes scheduling, conflict resolution, and advanced features
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import (
    Batch, Subject, StaffAssignment, Availability, Timetable, 
    Comment, Room, AdminNotification, AuditLog, User
)
from .serializers import (
    BatchSerializer, SubjectSerializer, StaffAssignmentSerializer,
    AvailabilitySerializer, TimetableSerializer, CommentSerializer,
    RoomSerializer, AdminNotificationSerializer, AuditLogSerializer
)
from .services.scheduling_service import SchedulingService, ConflictResolutionService
from .utils.notifications import send_email_notification


class TimetableGenerationView(APIView):
    """Advanced timetable generation and management"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        """Generate timetable for a batch"""
        batch_id = request.data.get('batch_id')
        force_regenerate = request.data.get('force_regenerate', False)
        
        if not batch_id:
            return Response({
                'error': 'batch_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Initialize scheduling service
            scheduler = SchedulingService()
            
            # Generate timetable
            result = scheduler.generate_timetable(batch_id, force_regenerate)
            
            if result['success']:
                # Log successful generation
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Timetable',
                    record_id=batch_id,
                    new_values={'details': f'Generated timetable for batch {batch_id} with {result["total_slots"]} slots'}
                )
                
                return Response(result)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'Failed to generate timetable',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def generate_all_batches(self, request):
        """Generate timetables for all active batches"""
        try:
            active_batches = Batch.objects.filter(is_active=True)
            results = []
            
            scheduler = SchedulingService()
            
            for batch in active_batches:
                result = scheduler.generate_timetable(batch.id, force_regenerate=False)
                results.append({
                    'batch_id': batch.id,
                    'batch_name': batch.name,
                    'result': result
                })
            
            # Log bulk generation
            AuditLog.objects.create(
                user=request.user,
                action='CREATE',
                table_name='Timetable',
                record_id=0,
                new_values={'details': f'Generated timetables for {len(active_batches)} batches'}
            )
            
            return Response({
                'message': f'Generated timetables for {len(active_batches)} batches',
                'results': results
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to generate timetables for all batches',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConflictManagementView(APIView):
    """Conflict detection and resolution"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get conflicts for a specific batch"""
        batch_id = request.query_params.get('batch_id')
        
        if not batch_id:
            return Response({
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            conflicts = ConflictResolutionService.detect_conflicts(batch_id)
            
            return Response({
                'batch_id': batch_id,
                'conflicts': conflicts,
                'total_conflicts': len(conflicts)
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to detect conflicts',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Resolve conflicts for a batch"""
        batch_id = request.data.get('batch_id')
        auto_resolve = request.data.get('auto_resolve', False)
        
        if not batch_id:
            return Response({
                'error': 'batch_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if auto_resolve:
                # Auto-resolve conflicts
                result = ConflictResolutionService.auto_resolve_conflicts(batch_id)
                
                # Log conflict resolution
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    table_name='Timetable',
                    record_id=batch_id,
                    new_values={'details': f'Auto-resolved {result["resolved_count"]} conflicts for batch {batch_id}'}
                )
                
                return Response(result)
            else:
                # Manual conflict resolution (return conflicts for admin review)
                conflicts = ConflictResolutionService.detect_conflicts(batch_id)
                
                return Response({
                    'batch_id': batch_id,
                    'conflicts': conflicts,
                    'total_conflicts': len(conflicts),
                    'message': 'Conflicts detected. Manual resolution required.'
                })
                
        except Exception as e:
            return Response({
                'error': 'Failed to resolve conflicts',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdvancedTimetableViewSet(viewsets.ModelViewSet):
    """Advanced timetable operations"""
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_batch_weekly(self, request):
        """Get weekly timetable view for a batch"""
        batch_id = request.query_params.get('batch_id')
        
        if not batch_id:
            return Response({
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            timetables = Timetable.objects.filter(batch_id=batch_id).order_by('day_of_week', 'start_time')
            
            # Organize by day
            weekly_schedule = {}
            # Use day-of-week strings to match model values
            weekly_schedule = {
                'monday': [], 'tuesday': [], 'wednesday': [], 'thursday': [],
                'friday': [], 'saturday': [], 'sunday': []
            }
            
            for tt in timetables:
                weekly_schedule[tt.day_of_week].append({
                    'id': tt.id,
                    'subject': tt.subject.name,
                    'subject_code': tt.subject.code,
                    'component_type': tt.component_type,
                    'start_time': tt.start_time,
                    'end_time': tt.end_time,
                    'room': tt.room.name if tt.room else None,
                    'staff': f"{tt.staff.first_name} {tt.staff.last_name}"
                })
            
            return Response({
                'batch_id': batch_id,
                'weekly_schedule': weekly_schedule
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to get weekly timetable',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def by_staff_weekly(self, request):
        """Get weekly timetable view for a staff member"""
        staff_id = request.query_params.get('staff_id')
        
        if not staff_id:
            return Response({
                'error': 'staff_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            timetables = Timetable.objects.filter(staff_id=staff_id).order_by('day_of_week', 'start_time')
            
            # Organize by day
            weekly_schedule = {}
            weekly_schedule = {
                'monday': [], 'tuesday': [], 'wednesday': [], 'thursday': [],
                'friday': [], 'saturday': [], 'sunday': []
            }
            
            for tt in timetables:
                weekly_schedule[tt.day_of_week].append({
                    'id': tt.id,
                    'subject': tt.subject.name,
                    'batch': tt.batch.name,
                    'component_type': tt.component_type,
                    'start_time': tt.start_time,
                    'end_time': tt.end_time,
                    'room': tt.room.name if tt.room else None
                })
            
            return Response({
                'staff_id': staff_id,
                'weekly_schedule': weekly_schedule
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to get staff weekly timetable',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def export_pdf(self, request):
        """Export timetable as PDF (placeholder for future implementation)"""
        batch_id = request.query_params.get('batch_id')
        
        if not batch_id:
            return Response({
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # This would generate and return a PDF file
        # For now, return a placeholder response
        return Response({
            'message': 'PDF export feature will be implemented in Phase 3',
            'batch_id': batch_id
        })
    
    @action(detail=False, methods=['get'])
    def export_ics(self, request):
        """Export timetable as ICS calendar file"""
        batch_id = request.query_params.get('batch_id')
        
        if not batch_id:
            return Response({
                'error': 'batch_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            timetables = Timetable.objects.filter(batch_id=batch_id).order_by('day_of_week', 'start_time')
            batch = get_object_or_404(Batch, id=batch_id)
            ics_content = self._generate_ics_for_batch(batch, timetables)
            from django.http import HttpResponse
            response = HttpResponse(ics_content, content_type='text/calendar')
            response['Content-Disposition'] = f'attachment; filename="timetable_batch_{batch_id}.ics"'
            return response
        except Exception as e:
            return Response({'error': 'Failed to export ICS', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StaffSchedulingView(APIView):
    """Advanced staff scheduling and availability management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get staff scheduling information"""
        staff_id = request.query_params.get('staff_id')
        
        if not staff_id:
            return Response({
                'error': 'staff_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get staff assignments
            assignments = StaffAssignment.objects.filter(
                staff_id=staff_id,
                is_active=True
            ).select_related('subject', 'batch')
            
            # Get availability
            availability = Availability.objects.filter(
                staff_id=staff_id,
                is_available=True
            )
            
            # Get current teaching schedule
            teaching_schedule = Timetable.objects.filter(
                staff_id=staff_id
            ).select_related('subject', 'batch', 'room').order_by('day_of_week', 'start_time')
            
            # Calculate workload
            # Compute total hours from start and end times
            def hours_between(tt):
                start_minutes = tt.start_time.hour * 60 + tt.start_time.minute
                end_minutes = tt.end_time.hour * 60 + tt.end_time.minute
                return max(0, (end_minutes - start_minutes) / 60)
            total_hours = sum(hours_between(tt) for tt in teaching_schedule)
            
            return Response({
                'staff_id': staff_id,
                'assignments': StaffAssignmentSerializer(assignments, many=True).data,
                'availability': AvailabilitySerializer(availability, many=True).data,
                'teaching_schedule': TimetableSerializer(teaching_schedule, many=True).data,
                'workload': {
                    'total_hours': total_hours,
                    'total_classes': len(teaching_schedule)
                }
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to get staff scheduling information',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """Update staff availability"""
        staff_id = request.data.get('staff_id')
        availability_data = request.data.get('availability', [])
        
        if not staff_id:
            return Response({
                'error': 'staff_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Clear existing availability
                Availability.objects.filter(staff_id=staff_id).delete()
                
                # Create new availability entries
                for avail_data in availability_data:
                    Availability.objects.create(
                        staff_id=staff_id,
                        day_of_week=avail_data['day_of_week'],
                        start_time=avail_data['start_time'],
                        end_time=avail_data['end_time'],
                    availability_type=avail_data.get('availability_type', 'weekday'),
                    is_available=True
                    )
                
                # Log availability update
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    table_name='Availability',
                    record_id=staff_id,
                    new_values={'details': f'Updated availability for staff {staff_id}'}
                )
                
                return Response({
                    'message': 'Staff availability updated successfully',
                    'staff_id': staff_id
                })
                
        except Exception as e:
            return Response({
                'error': 'Failed to update staff availability',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BatchManagementView(APIView):
    """Advanced batch management operations"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        """Create a new batch with subjects"""
        batch_data = request.data.get('batch', {})
        subjects_data = request.data.get('subjects', [])
        
        try:
            with transaction.atomic():
                # Create batch
                batch = Batch.objects.create(**batch_data)
                
                # Create subjects
                created_subjects = []
                for subject_data in subjects_data:
                    subject_data['batch'] = batch
                    subject = Subject.objects.create(**subject_data)
                    created_subjects.append(subject)
                
                # Log batch creation
                AuditLog.objects.create(
                    user=request.user,
                    action='CREATE',
                    table_name='Batch',
                    record_id=batch.id,
                    new_values={'details': f'Created batch {batch.name} with {len(created_subjects)} subjects'}
                )
                
                return Response({
                    'message': 'Batch created successfully',
                    'batch': BatchSerializer(batch).data,
                    'subjects': SubjectSerializer(created_subjects, many=True).data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': 'Failed to create batch',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def assign_staff(self, request):
        """Assign staff to subjects for a batch"""
        batch_id = request.data.get('batch_id')
        assignments_data = request.data.get('assignments', [])
        
        if not batch_id:
            return Response({
                'error': 'batch_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Clear existing assignments for this batch
                StaffAssignment.objects.filter(batch_id=batch_id).delete()
                
                # Create new assignments
                created_assignments = []
                for assignment_data in assignments_data:
                    assignment_data['batch_id'] = batch_id
                    assignment = StaffAssignment.objects.create(**assignment_data)
                    created_assignments.append(assignment)
                
                # Log staff assignment
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    table_name='StaffAssignment',
                    record_id=batch_id,
                    new_values={'details': f'Assigned {len(created_assignments)} staff members to batch {batch_id}'}
                )
                
                return Response({
                    'message': 'Staff assignments updated successfully',
                    'batch_id': batch_id,
                    'assignments': StaffAssignmentSerializer(created_assignments, many=True).data
                })
                
        except Exception as e:
            return Response({
                'error': 'Failed to assign staff',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AnalyticsView(APIView):
    """Analytics and reporting for the timetable system"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get system analytics"""
        try:
            # Calculate various metrics
            total_batches = Batch.objects.filter(is_active=True).count()
            # Subject model does not have is_active in current schema
            total_subjects = Subject.objects.count()
            total_staff = User.objects.filter(role='staff', is_active=True).count()
            total_students = User.objects.filter(role='student', is_active=True).count()
            total_timetables = Timetable.objects.count()
            total_rooms = Room.objects.filter(is_active=True).count()
            
            # Get recent activity
            recent_activities = AuditLog.objects.order_by('-timestamp')[:10]
            
            # Get conflict statistics
            all_conflicts = []
            for batch in Batch.objects.filter(is_active=True):
                conflicts = ConflictResolutionService.detect_conflicts(batch.id)
                all_conflicts.extend(conflicts)
            
            return Response({
                'overview': {
                    'total_batches': total_batches,
                    'total_subjects': total_subjects,
                    'total_staff': total_staff,
                    'total_students': total_students,
                    'total_timetables': total_timetables,
                    'total_rooms': total_rooms
                },
                'recent_activities': AuditLogSerializer(recent_activities, many=True).data,
                'conflicts': {
                    'total_conflicts': len(all_conflicts),
                    'conflict_types': self._count_conflict_types(all_conflicts)
                }
            })
            
        except Exception as e:
            return Response({
                'error': 'Failed to get analytics',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _count_conflict_types(self, conflicts):
        """Count conflicts by type"""
        conflict_counts = {}
        for conflict in conflicts:
            conflict_type = conflict['type']
            conflict_counts[conflict_type] = conflict_counts.get(conflict_type, 0) + 1
        return conflict_counts

    def _generate_ics_for_batch(self, batch, timetables):
        """Generate ICS content for a batch timetable."""
        def to_ics_datetime(date_obj, time_obj):
            return f"{date_obj.strftime('%Y%m%d')}{time_obj.strftime('%H%M%S')}"

        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        byday_map = {
            'monday': 'MO', 'tuesday': 'TU', 'wednesday': 'WE',
            'thursday': 'TH', 'friday': 'FR', 'saturday': 'SA', 'sunday': 'SU'
        }

        from datetime import timedelta
        import uuid
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//NorthernUni//Timetable//EN'
        ]
        # choose the first week start date
        start_date = batch.start_date
        for tt in timetables:
            # compute first occurrence date on/after batch.start_date for the day
            delta_days = (day_map[tt.day_of_week] - start_date.weekday()) % 7
            first_date = start_date + timedelta(days=delta_days)
            uid = str(uuid.uuid4())
            summary = f"{tt.subject.code} {tt.subject.name} ({tt.component_type})"
            location = tt.room.name if tt.room else ''
            description = f"Batch: {batch.name} | Staff: {tt.staff.first_name} {tt.staff.last_name}"
            dtstart = to_ics_datetime(first_date, tt.start_time)
            dtend = to_ics_datetime(first_date, tt.end_time)

            until_date = batch.end_date.strftime('%Y%m%d')
            lines.extend([
                'BEGIN:VEVENT',
                f'UID:{uid}',
                f'SUMMARY:{summary}',
                f'DESCRIPTION:{description}',
                f'LOCATION:{location}',
                f'DTSTART:{dtstart}',
                f'DTEND:{dtend}',
                f"RRULE:FREQ=WEEKLY;BYDAY={byday_map[tt.day_of_week]};UNTIL={until_date}T235959Z",
                'END:VEVENT'
            ])
        lines.append('END:VCALENDAR')
        return "\r\n".join(lines)
