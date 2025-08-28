"""
Scheduling Algorithm Service for University Timetable Management
Implements constraint satisfaction and conflict resolution algorithms
"""

import logging
from datetime import time, datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import (
    Batch, Subject, StaffAssignment, Availability, Timetable, 
    Room, Comment, AuditLog, User
)

logger = logging.getLogger(__name__)


class SchedulingService:
    """Main scheduling service for timetable generation"""
    
    def __init__(self):
        self.conflicts = []
        self.scheduled_slots = set()
        self.staff_schedules = {}
        self.room_schedules = {}
        self.batch_schedules = {}
    
    def generate_timetable(self, batch_id: int, force_regenerate: bool = False) -> Dict:
        """
        Generate complete timetable for a batch
        
        Args:
            batch_id: ID of the batch to schedule
            force_regenerate: Whether to regenerate existing timetable
            
        Returns:
            Dict containing success status and generated timetables
        """
        try:
            batch = Batch.objects.get(id=batch_id)
            
            if not force_regenerate and Timetable.objects.filter(batch=batch).exists():
                return {
                    'success': False,
                    'message': 'Timetable already exists. Use force_regenerate=True to override.'
                }
            
            # Clear existing timetable if regenerating
            if force_regenerate:
                Timetable.objects.filter(batch=batch).delete()
                self._log_action('DELETE', f'Deleted existing timetable for batch {batch.name}')
            
            # Initialize scheduling state
            self._initialize_scheduling_state(batch)
            
            # Get subjects for the batch (Subject has no is_active field)
            subjects = Subject.objects.filter(batch=batch)
            if not subjects.exists():
                return {
                    'success': False,
                    'message': f'No subjects found for batch {batch.name}'
                }
            
            # Generate timetable using constraint satisfaction algorithm
            timetables = self._generate_schedule(batch, subjects)
            
            if not timetables:
                return {
                    'success': False,
                    'message': 'Failed to generate timetable due to conflicts',
                    'conflicts': self.conflicts
                }
            
            # Save generated timetables
            saved_timetables = self._save_timetables(timetables)
            
            # Log successful generation
            self._log_action('CREATE', f'Generated timetable for batch {batch.name} with {len(saved_timetables)} slots')
            
            return {
                'success': True,
                'message': f'Successfully generated timetable for batch {batch.name}',
                'timetables': saved_timetables,
                'total_slots': len(saved_timetables),
                'conflicts_resolved': len(self.conflicts)
            }
            
        except Batch.DoesNotExist:
            return {'success': False, 'message': 'Batch not found'}
        except Exception as e:
            logger.error(f"Error generating timetable: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def _initialize_scheduling_state(self, batch: Batch):
        """Initialize scheduling state for a new batch"""
        self.conflicts = []
        self.scheduled_slots = set()
        self.staff_schedules = {}
        self.room_schedules = {}
        self.batch_schedules = {}
        
        # Get existing timetables for conflict checking
        existing_timetables = Timetable.objects.all()
        for tt in existing_timetables:
            slot_key = (tt.day_of_week, tt.start_time, tt.end_time)
            self.scheduled_slots.add(slot_key)
            
            # Track staff schedules
            if tt.staff_id not in self.staff_schedules:
                self.staff_schedules[tt.staff_id] = set()
            self.staff_schedules[tt.staff_id].add(slot_key)
            
            # Track room schedules
            if tt.room_id not in self.room_schedules:
                self.room_schedules[tt.room_id] = set()
            self.room_schedules[tt.room_id].add(slot_key)
            
            # Track batch schedules
            if tt.batch_id not in self.batch_schedules:
                self.batch_schedules[tt.batch_id] = set()
            self.batch_schedules[tt.batch_id].add(slot_key)
    
    def _generate_schedule(self, batch: Batch, subjects: List[Subject]) -> List[Dict]:
        """
        Generate schedule using constraint satisfaction algorithm
        
        Algorithm:
        1. Sort subjects by priority (Lecture > Tutorial > Lab)
        2. For each subject, find available slots considering:
           - Staff availability
           - Room availability
           - Batch time constraints
           - No overlapping slots for same staff/batch/room
        3. Use backtracking for conflict resolution
        """
        timetables = []
        
        # Sort subjects by priority
        prioritized_subjects = self._prioritize_subjects(subjects)
        
        # Generate schedule for each subject
        for subject in prioritized_subjects:
            subject_timetables = self._schedule_subject(batch, subject)
            if subject_timetables:
                timetables.extend(subject_timetables)
            else:
                # Log conflict for this subject
                self.conflicts.append({
                    'subject': subject.name,
                    'batch': batch.name,
                    'type': 'SCHEDULING_FAILED',
                    'message': f'Could not schedule {subject.name} for {batch.name}'
                })
        
        return timetables
    
    def _prioritize_subjects(self, subjects: List[Subject]) -> List[Subject]:
        """Sort subjects by priority: Lecture > Tutorial > Lab"""
        priority_order = {
            'lecture': 1,
            'tutorial': 2,
            'lab': 3
        }
        
        def get_priority(subject):
            # Calculate total hours for each component type
            total_lecture = subject.lecture_duration or 0
            total_tutorial = subject.tutorial_duration or 0
            total_lab = subject.lab_duration or 0
            
            # Return highest priority component
            if total_lecture > 0:
                return priority_order['lecture']
            elif total_tutorial > 0:
                return priority_order['tutorial']
            else:
                return priority_order['lab']
        
        return sorted(subjects, key=get_priority)
    
    def _schedule_subject(self, batch: Batch, subject: Subject) -> List[Dict]:
        """Schedule a single subject with all its components"""
        timetables = []
        
        # Get staff assignments for this subject
        staff_assignments = StaffAssignment.objects.filter(
            subject=subject,
            batch=batch,
            is_active=True
        )
        
        if not staff_assignments.exists():
            self.conflicts.append({
                'subject': subject.name,
                'batch': batch.name,
                'type': 'NO_STAFF',
                'message': f'No staff assigned to {subject.name} for {batch.name}'
            })
            return []
        
        # Schedule each component type
        components = [
            ('lecture', subject.lecture_duration),
            ('tutorial', subject.tutorial_duration),
            ('lab', subject.lab_duration)
        ]
        
        for component_type, duration in components:
            if duration and duration > 0:
                component_timetables = self._schedule_component(
                    batch, subject, component_type, duration, staff_assignments
                )
                if component_timetables:
                    timetables.extend(component_timetables)
                else:
                    self.conflicts.append({
                        'subject': subject.name,
                        'component': component_type,
                        'batch': batch.name,
                        'type': 'COMPONENT_SCHEDULING_FAILED',
                        'message': f'Could not schedule {component_type} for {subject.name}'
                    })
        
        return timetables
    
    def _schedule_component(self, batch: Batch, subject: Subject, component_type: str, 
                           duration: int, staff_assignments: List[StaffAssignment]) -> List[Dict]:
        """Schedule a specific component of a subject"""
        timetables = []
        required_slots = self._calculate_required_slots(duration)
        
        # Try to schedule each required slot
        for slot_index in range(required_slots):
            slot_timetable = self._find_available_slot(
                batch, subject, component_type, staff_assignments
            )
            
            if slot_timetable:
                timetables.append(slot_timetable)
            else:
                # Try to resolve conflict by adjusting existing schedules
                if self._resolve_conflict(batch, subject, component_type, staff_assignments):
                    slot_timetable = self._find_available_slot(
                        batch, subject, component_type, staff_assignments
                    )
                    if slot_timetable:
                        timetables.append(slot_timetable)
                    else:
                        return []  # Failed to resolve conflict
                else:
                    return []  # Failed to resolve conflict
        
        return timetables
    
    def _calculate_required_slots(self, duration: int) -> int:
        """Calculate number of 1-hour slots needed for a duration in minutes (60-120)."""
        hours = max(1, min(2, duration // 60))
        return hours
    
    def _find_available_slot(self, batch: Batch, subject: Subject, component_type: str,
                            staff_assignments: List[StaffAssignment]) -> Optional[Dict]:
        """Find an available time slot for scheduling"""
        # Get batch time constraints
        batch_times = self._get_batch_time_constraints(batch)
        
        # Try each day and time slot
        for day in range(1, 8):  # Monday = 1, Sunday = 7
            if day == 6:  # Saturday
                start_time = time(8, 30)
                end_time = time(20, 0)
            elif day == 7:  # Sunday
                start_time = time(8, 30)
                end_time = time(20, 0)
            else:  # Weekdays
                start_time = time(8, 30)
                end_time = time(17, 30)
            
            # Try each hour slot
            current_time = start_time
            while current_time < end_time:
                slot_end = self._add_hours(current_time, 1)
                
                if slot_end <= end_time:
                    day_name = self._map_day_number_to_name(day)
                    slot_key = (day_name, current_time, slot_end)
                    
                    if self._is_slot_available(batch, subject, slot_key, staff_assignments):
                        # Find available room
                        room = self._find_available_room(slot_key)
                        if room:
                            # Find available staff
                            staff = self._find_available_staff(slot_key, staff_assignments)
                            if staff:
                                return {
                                    'batch': batch,
                                    'subject': subject,
                                    'component_type': component_type,
                                    'day_of_week': day_name,
                                    'start_time': current_time,
                                    'end_time': slot_end,
                                    'room': room,
                                    'staff': staff
                                }
                
                current_time = slot_end
        
        return None
    
    def _get_batch_time_constraints(self, batch: Batch) -> Dict:
        """Get time constraints for a batch"""
        return {
            'weekday_start': time(8, 30),
            'weekday_end': time(17, 30),
            'weekend_start': time(8, 30),
            'weekend_end': time(20, 0),
            'evening_start': time(17, 30),
            'evening_end': time(20, 0)
        }
    
    def _add_hours(self, time_obj: time, hours: int) -> time:
        """Add hours to a time object"""
        total_minutes = time_obj.hour * 60 + time_obj.minute + hours * 60
        new_hour = (total_minutes // 60) % 24
        new_minute = total_minutes % 60
        return time(new_hour, new_minute)
    
    def _is_slot_available(self, batch: Batch, subject: Subject, slot_key: Tuple,
                          staff_assignments: List[StaffAssignment]) -> bool:
        """Check if a time slot is available for scheduling"""
        day, start_time, end_time = slot_key
        
        # Check if slot is already scheduled for this batch
        if slot_key in self.batch_schedules.get(batch.id, set()):
            return False
        
        # Check if any staff is already scheduled at this time
        for assignment in staff_assignments:
            if assignment.staff_id in self.staff_schedules:
                if slot_key in self.staff_schedules[assignment.staff_id]:
                    return False
        
        return True
    
    def _find_available_room(self, slot_key: Tuple) -> Optional[Room]:
        """Find an available room for a time slot"""
        available_rooms = Room.objects.filter(is_active=True)
        
        for room in available_rooms:
            if room.id not in self.room_schedules or slot_key not in self.room_schedules[room.id]:
                return room
        
        return None
    
    def _find_available_staff(self, slot_key: Tuple, staff_assignments: List[StaffAssignment]) -> Optional[User]:
        """Find available staff for a time slot"""
        for assignment in staff_assignments:
            if assignment.staff_id not in self.staff_schedules or slot_key not in self.staff_schedules[assignment.staff_id]:
                # Check staff availability preferences
                if self._check_staff_availability(assignment.staff, slot_key):
                    return assignment.staff
        
        return None
    
    def _check_staff_availability(self, staff: User, slot_key: Tuple) -> bool:
        """Check if staff member is available for a time slot"""
        day, start_time, end_time = slot_key
        
        # Check staff availability preferences
        availability = Availability.objects.filter(
            staff=staff,
            day_of_week=day,
            start_time__lte=start_time,
            end_time__gte=end_time,
            is_active=True
        ).first()
        
        return availability is not None
    
    def _resolve_conflict(self, batch: Batch, subject: Subject, component_type: str,
                         staff_assignments: List[StaffAssignment]) -> bool:
        """Attempt to resolve scheduling conflicts by adjusting existing schedules"""
        # This is a simplified conflict resolution strategy
        # In a real implementation, this would be more sophisticated
        
        # Try to find alternative slots by checking if any existing slots can be moved
        existing_timetables = Timetable.objects.filter(batch=batch)
        
        for existing_tt in existing_timetables:
            # Check if this slot can be moved to accommodate the new subject
            if self._can_move_slot(existing_tt, subject, component_type, staff_assignments):
                # Move the existing slot
                new_slot = self._find_alternative_slot(existing_tt)
                if new_slot:
                    existing_tt.day_of_week = new_slot[0]
                    existing_tt.start_time = new_slot[1]
                    existing_tt.end_time = new_slot[2]
                    existing_tt.save()
                    
                    # Update scheduling state
                    self._update_scheduling_state(existing_tt, new_slot)
                    return True
        
        return False
    
    def _can_move_slot(self, timetable: Timetable, subject: Subject, component_type: str,
                       staff_assignments: List[StaffAssignment]) -> bool:
        """Check if a timetable slot can be moved"""
        # Check if the slot is flexible (e.g., not a critical lecture)
        return timetable.component_type in ['tutorial', 'lab']
    
    def _find_alternative_slot(self, timetable: Timetable) -> Optional[Tuple]:
        """Find an alternative slot for a timetable entry"""
        # Simplified alternative slot finding
        # In reality, this would check all possible slots systematically
        
        batch_times = self._get_batch_time_constraints(timetable.batch)
        
        for day in range(1, 8):
            if self._map_day_number_to_name(day) == timetable.day_of_week:
                continue
                
            if day in [6, 7]:  # Weekend
                start_time = batch_times['weekend_start']
                end_time = batch_times['weekend_end']
            else:  # Weekday
                start_time = batch_times['weekday_start']
                end_time = batch_times['weekday_end']
            
            current_time = start_time
            while current_time < end_time:
                slot_end = self._add_hours(current_time, 1)
                
                if slot_end <= end_time:
                    day_name = self._map_day_number_to_name(day)
                    slot_key = (day_name, current_time, slot_end)
                    
                    # Check if this slot is available
                    if self._is_slot_available(timetable.batch, timetable.subject, slot_key, []):
                        room = self._find_available_room(slot_key)
                        if room:
                            return (day_name, current_time, slot_end)
                
                current_time = slot_end
        
        return None
    
    def _update_scheduling_state(self, timetable: Timetable, new_slot: Tuple):
        """Update internal scheduling state after moving a slot"""
        # Remove old slot
        old_slot = (timetable.day_of_week, timetable.start_time, timetable.end_time)
        if old_slot in self.scheduled_slots:
            self.scheduled_slots.remove(old_slot)
        
        # Add new slot
        self.scheduled_slots.add(new_slot)
        
        # Update staff schedules
        if timetable.staff_id in self.staff_schedules:
            if old_slot in self.staff_schedules[timetable.staff_id]:
                self.staff_schedules[timetable.staff_id].remove(old_slot)
            self.staff_schedules[timetable.staff_id].add(new_slot)
        
        # Update room schedules
        if timetable.room_id in self.room_schedules:
            if old_slot in self.room_schedules[timetable.room_id]:
                self.room_schedules[timetable.room_id].remove(old_slot)
            self.room_schedules[timetable.room_id].add(new_slot)
        
        # Update batch schedules
        if timetable.batch_id in self.batch_schedules:
            if old_slot in self.batch_schedules[timetable.batch_id]:
                self.batch_schedules[timetable.batch_id].remove(old_slot)
            self.batch_schedules[timetable.batch_id].add(new_slot)
    
    def _save_timetables(self, timetables: List[Dict]) -> List[Timetable]:
        """Save generated timetables to database"""
        saved_timetables = []
        
        with transaction.atomic():
            for tt_data in timetables:
                timetable = Timetable.objects.create(
                    batch=tt_data['batch'],
                    subject=tt_data['subject'],
                    component_type=tt_data['component_type'],
                    day_of_week=tt_data['day_of_week'],
                    start_time=tt_data['start_time'],
                    end_time=tt_data['end_time'],
                    room=tt_data['room'],
                    staff=tt_data['staff'],
                    duration=tt_data['duration']
                )
                
                saved_timetables.append(timetable)
                
                # Update scheduling state
                slot_key = (timetable.day_of_week, timetable.start_time, timetable.end_time)
                self.scheduled_slots.add(slot_key)
                
                if timetable.staff_id not in self.staff_schedules:
                    self.staff_schedules[timetable.staff_id] = set()
                self.staff_schedules[timetable.staff_id].add(slot_key)
                
                if timetable.room_id not in self.room_schedules:
                    self.room_schedules[timetable.room_id] = set()
                self.room_schedules[timetable.room_id].add(slot_key)
                
                if timetable.batch_id not in self.batch_schedules:
                    self.batch_schedules[timetable.batch_id] = set()
                self.batch_schedules[timetable.batch_id].add(slot_key)
        
        return saved_timetables
    
    def _log_action(self, action: str, details: str):
        """Log scheduling actions for audit purposes"""
        try:
            AuditLog.objects.create(
                user=None,  # System action
                action=action,
                table_name='Timetable',
                record_id=0,
                new_values={'details': details}
            )
        except Exception as e:
            logger.error(f"Failed to log action: {e}")

    def _map_day_number_to_name(self, day_number: int) -> str:
        """Map ISO-like day number (1=Mon..7=Sun) to model choice string."""
        mapping = {
            1: 'monday',
            2: 'tuesday',
            3: 'wednesday',
            4: 'thursday',
            5: 'friday',
            6: 'saturday',
            7: 'sunday',
        }
        return mapping.get(day_number, 'monday')


class ConflictResolutionService:
    """Service for resolving scheduling conflicts"""
    
    @staticmethod
    def detect_conflicts(batch_id: int) -> List[Dict]:
        """Detect all conflicts in a batch's timetable"""
        conflicts = []
        
        try:
            timetables = Timetable.objects.filter(batch_id=batch_id).order_by('day_of_week', 'start_time')
            
            # Check for overlapping slots
            for i, tt1 in enumerate(timetables):
                for tt2 in timetables[i+1:]:
                    if tt1.day_of_week == tt2.day_of_week:
                        if (tt1.start_time < tt2.end_time and tt1.end_time > tt2.start_time):
                            conflicts.append({
                                'type': 'TIME_OVERLAP',
                                'message': f'Time overlap between {tt1.subject.name} and {tt2.subject.name}',
                                'timetable1': tt1.id,
                                'timetable2': tt2.id,
                                'day': tt1.day_of_week,
                                'time_range': f'{tt1.start_time} - {tt1.end_time} vs {tt2.start_time} - {tt2.end_time}'
                            })
            
            # Check for staff conflicts
            staff_schedules = {}
            for tt in timetables:
                if tt.staff_id not in staff_schedules:
                    staff_schedules[tt.staff_id] = []
                staff_schedules[tt.staff_id].append(tt)
            
            for staff_id, staff_tts in staff_schedules.items():
                for i, tt1 in enumerate(staff_tts):
                    for tt2 in staff_tts[i+1:]:
                        if tt1.day_of_week == tt2.day_of_week:
                            if (tt1.start_time < tt2.end_time and tt1.end_time > tt2.start_time):
                                conflicts.append({
                                    'type': 'STAFF_CONFLICT',
                                    'message': f'Staff {tt1.staff.username} has overlapping classes',
                                    'timetable1': tt1.id,
                                    'timetable2': tt2.id,
                                    'staff': tt1.staff.username
                                })
            
            # Check for room conflicts
            room_schedules = {}
            for tt in timetables:
                if tt.room_id not in room_schedules:
                    room_schedules[tt.room_id] = []
                room_schedules[tt.room_id].append(tt)
            
            for room_id, room_tts in room_schedules.items():
                for i, tt1 in enumerate(room_tts):
                    for tt2 in room_tts[i+1:]:
                        if tt1.day_of_week == tt2.day_of_week:
                            if (tt1.start_time < tt2.end_time and tt1.end_time > tt2.start_time):
                                conflicts.append({
                                    'type': 'ROOM_CONFLICT',
                                    'message': f'Room {tt1.room.name} has overlapping classes',
                                    'timetable1': tt1.id,
                                    'timetable2': tt2.id,
                                    'room': tt1.room.name
                                })
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return []
    
    @staticmethod
    def auto_resolve_conflicts(batch_id: int) -> Dict:
        """Automatically resolve detected conflicts"""
        conflicts = ConflictResolutionService.detect_conflicts(batch_id)
        
        if not conflicts:
            return {
                'success': True,
                'message': 'No conflicts detected',
                'resolved_count': 0
            }
        
        resolved_count = 0
        
        for conflict in conflicts:
            if ConflictResolutionService._resolve_single_conflict(conflict):
                resolved_count += 1
        
        return {
            'success': True,
            'message': f'Resolved {resolved_count} out of {len(conflicts)} conflicts',
            'resolved_count': resolved_count,
            'total_conflicts': len(conflicts)
        }
    
    @staticmethod
    def _resolve_single_conflict(conflict: Dict) -> bool:
        """Resolve a single conflict"""
        try:
            if conflict['type'] == 'TIME_OVERLAP':
                return ConflictResolutionService._resolve_time_overlap(conflict)
            elif conflict['type'] == 'STAFF_CONFLICT':
                return ConflictResolutionService._resolve_staff_conflict(conflict)
            elif conflict['type'] == 'ROOM_CONFLICT':
                return ConflictResolutionService._resolve_room_conflict(conflict)
            else:
                return False
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return False
    
    @staticmethod
    def _resolve_time_overlap(conflict: Dict) -> bool:
        """Resolve time overlap conflict"""
        try:
            tt1_id = conflict.get('timetable1')
            tt2_id = conflict.get('timetable2')
            if not tt1_id or not tt2_id:
                return False
            tt1 = Timetable.objects.get(id=tt1_id)
            tt2 = Timetable.objects.get(id=tt2_id)
            # Attempt to move the later-starting one by +1 hour within batch bounds
            target = tt1 if tt1.start_time > tt2.start_time else tt2
            service = SchedulingService()
            batch_times = service._get_batch_time_constraints(target.batch)
            new_start = service._add_hours(target.start_time, 1)
            new_end = service._add_hours(target.end_time, 1)
            day_name = target.day_of_week
            if (day_name in ['saturday', 'sunday'] and new_end <= batch_times['weekend_end']) or \
               (day_name in ['monday','tuesday','wednesday','thursday','friday'] and new_end <= batch_times['weekday_end']):
                # Check availability for staff and room
                slot_key = (day_name, new_start, new_end)
                if service._is_slot_available(target.batch, target.subject, slot_key, []):
                    room_ok = (target.room_id is None) or (target.room_id in service.room_schedules and slot_key not in service.room_schedules[target.room_id])
                    if room_ok:
                        target.start_time = new_start
                        target.end_time = new_end
                        target.save()
                        return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def _resolve_staff_conflict(conflict: Dict) -> bool:
        """Resolve staff conflict"""
        # Implementation would involve reassigning staff or rescheduling
        return False
    
    @staticmethod
    def _resolve_room_conflict(conflict: Dict) -> bool:
        """Resolve room conflict"""
        try:
            tt1_id = conflict.get('timetable1')
            tt2_id = conflict.get('timetable2')
            if not tt1_id or not tt2_id:
                return False
            tt1 = Timetable.objects.get(id=tt1_id)
            tt2 = Timetable.objects.get(id=tt2_id)
            # Try to find an alternative available room for tt2
            service = SchedulingService()
            slot_key = (tt2.day_of_week, tt2.start_time, tt2.end_time)
            room = service._find_available_room(slot_key)
            if room and (not tt1.room_id or room.id != tt1.room_id):
                tt2.room = room
                tt2.save()
                return True
            return False
        except Exception:
            return False
