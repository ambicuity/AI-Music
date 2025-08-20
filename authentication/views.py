from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from .models import UserProfile, UserFollowing, UserActivity, APIKey
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    UserSerializer, UserFollowingSerializer, UserActivitySerializer, APIKeySerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Update last active timestamp
        if hasattr(user, 'profile'):
            user.profile.last_active = timezone.now()
            user.profile.save()
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'token': token.key,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User logout endpoint"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """User profile view"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class PublicUserListView(generics.ListAPIView):
    """Public user list for discovery"""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return User.objects.filter(
            profile__is_public=True,
            is_active=True
        ).select_related('profile').order_by('-profile__reputation_score')


class UserDetailView(generics.RetrieveAPIView):
    """Public user detail view"""
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    lookup_field = 'username'
    
    def get_queryset(self):
        return User.objects.filter(
            profile__is_public=True,
            is_active=True
        ).select_related('profile')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_user(request, username):
    """Follow/unfollow a user"""
    target_user = get_object_or_404(User, username=username)
    
    if target_user == request.user:
        return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
    
    following, created = UserFollowing.objects.get_or_create(
        follower=request.user,
        following=target_user
    )
    
    if not created:
        following.delete()
        return Response({'message': f'Unfollowed {username}'}, status=status.HTTP_200_OK)
    else:
        # Create activity record
        UserActivity.objects.create(
            user=request.user,
            activity_type='user_followed',
            content_type='user',
            object_id=target_user.id,
            metadata={'username': username}
        )
        return Response({'message': f'Following {username}'}, status=status.HTTP_201_CREATED)


class UserFollowersView(generics.ListAPIView):
    """List user's followers"""
    serializer_class = UserFollowingSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return UserFollowing.objects.filter(following=user).select_related('follower', 'following')


class UserFollowingView(generics.ListAPIView):
    """List users that a user is following"""
    serializer_class = UserFollowingSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        username = self.kwargs['username']
        user = get_object_or_404(User, username=username)
        return UserFollowing.objects.filter(follower=user).select_related('follower', 'following')


class UserActivityFeedView(generics.ListAPIView):
    """User's activity feed"""
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Get activities from users the current user follows
        following_users = UserFollowing.objects.filter(follower=user).values_list('following', flat=True)
        return UserActivity.objects.filter(
            user__in=following_users,
            is_public=True
        ).select_related('user').order_by('-created_at')[:50]


class APIKeyManagementView(generics.ListCreateAPIView):
    """Manage user's API keys for external services"""
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
