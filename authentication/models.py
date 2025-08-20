from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile with music preferences and social features"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Profile Information
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    
    # Music Preferences
    MUSIC_EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('professional', 'Professional'),
    ]
    
    favorite_genres = models.JSONField(default=list, help_text="List of favorite music genres")
    music_experience = models.CharField(
        max_length=20, 
        choices=MUSIC_EXPERIENCE_CHOICES, 
        default='beginner'
    )
    preferred_instruments = models.JSONField(default=list, help_text="List of preferred instruments")
    
    # Social Features
    is_public = models.BooleanField(default=True, help_text="Profile visibility")
    allow_collaboration = models.BooleanField(default=True)
    receive_notifications = models.BooleanField(default=True)
    
    # AI Preferences
    ai_creativity_level = models.FloatField(default=0.7, help_text="AI creativity preference (0-1)")
    preferred_ai_models = models.JSONField(default=list, help_text="Preferred AI model versions")
    
    # Activity Tracking
    total_compositions = models.PositiveIntegerField(default=0)
    total_collaborations = models.PositiveIntegerField(default=0)
    reputation_score = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(default=timezone.now)
    
    class Meta:
        indexes = [
            models.Index(fields=['reputation_score']),
            models.Index(fields=['last_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username}'s profile"


class UserFollowing(models.Model):
    """User following/followers relationship"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class UserActivity(models.Model):
    """Track user activities for social feed and recommendations"""
    ACTIVITY_TYPES = [
        ('composition_created', 'Created Composition'),
        ('composition_liked', 'Liked Composition'),
        ('user_followed', 'Followed User'),
        ('collaboration_joined', 'Joined Collaboration'),
        ('playlist_created', 'Created Playlist'),
        ('track_streamed', 'Streamed Track'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    content_type = models.CharField(max_length=50, blank=True)  # composition, track, user, etc.
    object_id = models.PositiveIntegerField(blank=True, null=True)
    metadata = models.JSONField(default=dict, help_text="Additional activity data")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()}"


class APIKey(models.Model):
    """User API keys for external service integrations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    service_name = models.CharField(max_length=50)  # spotify, apple_music, etc.
    api_key = models.CharField(max_length=500)
    refresh_token = models.CharField(max_length=500, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'service_name')
    
    def __str__(self):
        return f"{self.user.username} - {self.service_name}"
