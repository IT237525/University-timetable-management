from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import User, AuditLog
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    UserDetailSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with additional user data"""
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Add user information to response
            user = User.objects.get(username=request.data['username'])
            user_data = UserSerializer(user).data
            
            response.data.update({
                'user': user_data,
                'message': 'Login successful'
            })
            
            # Log successful login
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                table_name='User',
                record_id=user.id,
                details=f'User {user.username} logged in successfully'
            )
        
        return response


@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationView(APIView):
    """User registration endpoint with validation"""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Validate password strength
                password = serializer.validated_data['password']
                validate_password(password)
                
                with transaction.atomic():
                    # Create user
                    user = serializer.save()
                    
                    # Generate tokens
                    refresh = RefreshToken.for_user(user)
                    access_token = refresh.access_token
                    
                    # Log user creation
                    AuditLog.objects.create(
                        user=user,
                        action='CREATE',
                        table_name='User',
                        record_id=user.id,
                        details=f'New user {user.username} registered with role {user.role}'
                    )
                    
                    return Response({
                        'message': 'User registered successfully',
                        'user': UserSerializer(user).data,
                        'tokens': {
                            'access': str(access_token),
                            'refresh': str(refresh)
                        }
                    }, status=status.HTTP_201_CREATED)
                    
            except ValidationError as e:
                return Response({
                    'error': 'Password validation failed',
                    'details': e.messages
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    """User login endpoint with JWT tokens"""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Log successful login
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                table_name='User',
                record_id=user.id,
                details=f'User {user.username} logged in successfully'
            )
            
            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data,
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh)
                }
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """User profile management"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user profile"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update current user profile"""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            old_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'email': user.email
            }
            
            serializer.save()
            
            # Log profile update
            changes = []
            for field, old_value in old_data.items():
                new_value = getattr(user, field)
                if old_value != new_value:
                    changes.append(f'{field}: {old_value} -> {new_value}')
            
            if changes:
                AuditLog.objects.create(
                    user=user,
                    action='UPDATE',
                    table_name='User',
                    record_id=user.id,
                    details=f'Profile updated: {", ".join(changes)}'
                )
            
            return Response({
                'message': 'Profile updated successfully',
                'user': UserSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            return Response({
                'error': 'All password fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'error': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.check_password(current_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Validate new password strength
            validate_password(new_password)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Log password change
            AuditLog.objects.create(
                user=user,
                action='UPDATE',
                table_name='User',
                record_id=user.id,
                details='Password changed successfully'
            )
            
            return Response({
                'message': 'Password changed successfully'
            })
            
        except ValidationError as e:
            return Response({
                'error': 'Password validation failed',
                'details': e.messages
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log logout
            AuditLog.objects.create(
                user=request.user,
                action='LOGOUT',
                table_name='User',
                record_id=request.user.id,
                details=f'User {request.user.username} logged out'
            )
            
            return Response({
                'message': 'Logout successful'
            })
            
        except Exception as e:
            return Response({
                'error': 'Logout failed',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    """Refresh JWT token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        access_token = token.access_token
        
        return Response({
            'access': str(access_token)
        })
        
    except Exception as e:
        return Response({
            'error': 'Token refresh failed',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_activity_view(request):
    """Get user activity log"""
    user = request.user
    activities = AuditLog.objects.filter(user=user).order_by('-timestamp')[:50]
    
    activity_data = []
    for activity in activities:
        activity_data.append({
            'action': activity.action,
            'table': activity.table_name,
            'details': activity.details,
            'timestamp': activity.timestamp
        })
    
    return Response({
        'activities': activity_data,
        'total_count': AuditLog.objects.filter(user=user).count()
    })
