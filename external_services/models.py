from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ExternalServiceConfig(models.Model):
    """Configuration for external music services"""
    SERVICE_CHOICES = [
        ('spotify', 'Spotify'),
        ('apple_music', 'Apple Music'),
        ('youtube_music', 'YouTube Music'),
        ('soundcloud', 'SoundCloud'),
        ('bandcamp', 'Bandcamp'),
    ]
    
    name = models.CharField(max_length=50, choices=SERVICE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    
    # API Configuration
    api_base_url = models.URLField()
    client_id = models.CharField(max_length=200, blank=True)
    client_secret = models.CharField(max_length=200, blank=True)
    
    # Service capabilities
    supports_streaming = models.BooleanField(default=True)
    supports_search = models.BooleanField(default=True)
    supports_playlists = models.BooleanField(default=True)
    supports_recommendations = models.BooleanField(default=True)
    
    # Rate limiting
    requests_per_minute = models.PositiveIntegerField(default=100)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.display_name


class UserServiceConnection(models.Model):
    """User connections to external services"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_connections')
    service = models.ForeignKey(ExternalServiceConfig, on_delete=models.CASCADE)
    
    # OAuth tokens
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Service user info
    external_user_id = models.CharField(max_length=100)
    external_username = models.CharField(max_length=100, blank=True)
    
    # Permissions
    scopes = models.JSONField(default=list, help_text="Granted permission scopes")
    
    # Status
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'service')
    
    def __str__(self):
        return f"{self.user.username} - {self.service.display_name}"


class ExternalTrack(models.Model):
    """Tracks from external services"""
    service = models.ForeignKey(ExternalServiceConfig, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=200)
    
    # Basic metadata
    title = models.CharField(max_length=300)
    artist = models.CharField(max_length=300)
    album = models.CharField(max_length=300, blank=True)
    genre = models.CharField(max_length=100, blank=True)
    
    # Details
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    popularity = models.PositiveIntegerField(null=True, blank=True)
    
    # URLs
    external_url = models.URLField(blank=True)
    preview_url = models.URLField(blank=True)
    artwork_url = models.URLField(blank=True)
    
    # Audio features (if available from service)
    audio_features = models.JSONField(default=dict, blank=True)
    
    # Local processing
    is_analyzed = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('service', 'external_id')
        indexes = [
            models.Index(fields=['service', 'external_id']),
            models.Index(fields=['artist', 'title']),
        ]
    
    def __str__(self):
        return f"{self.artist} - {self.title} ({self.service.display_name})"


class ExternalPlaylist(models.Model):
    """Playlists from external services"""
    service = models.ForeignKey(ExternalServiceConfig, on_delete=models.CASCADE)
    user_connection = models.ForeignKey(UserServiceConnection, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=200)
    
    # Playlist metadata
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    
    # Stats
    track_count = models.PositiveIntegerField(default=0)
    followers_count = models.PositiveIntegerField(default=0)
    
    # URLs
    external_url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    
    # Sync info
    last_synced = models.DateTimeField(null=True, blank=True)
    is_synced = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('service', 'external_id')
    
    def __str__(self):
        return f"{self.name} ({self.service.display_name})"


class ExternalPlaylistTrack(models.Model):
    """Tracks in external playlists"""
    playlist = models.ForeignKey(ExternalPlaylist, on_delete=models.CASCADE, related_name='tracks')
    track = models.ForeignKey(ExternalTrack, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    added_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('playlist', 'track')
        ordering = ['position']


class RecommendationEngine(models.Model):
    """Recommendation engines from external services"""
    service = models.ForeignKey(ExternalServiceConfig, on_delete=models.CASCADE)
    user_connection = models.ForeignKey(UserServiceConnection, on_delete=models.CASCADE)
    
    # Engine configuration
    engine_name = models.CharField(max_length=100)
    parameters = models.JSONField(default=dict)
    
    # Last recommendation data
    last_recommendations = models.JSONField(default=list)
    last_updated = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    click_through_rate = models.FloatField(default=0.0)
    satisfaction_score = models.FloatField(default=0.0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('service', 'user_connection', 'engine_name')
    
    def __str__(self):
        return f"{self.engine_name} for {self.user_connection}"


class ServiceSyncJob(models.Model):
    """Background sync jobs for external services"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SYNC_TYPES = [
        ('playlists', 'Sync Playlists'),
        ('library', 'Sync Library'),
        ('recommendations', 'Sync Recommendations'),
        ('listening_history', 'Sync Listening History'),
    ]
    
    user_connection = models.ForeignKey(UserServiceConnection, on_delete=models.CASCADE)
    sync_type = models.CharField(max_length=30, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Progress tracking
    progress = models.FloatField(default=0.0)
    items_processed = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    
    # Results
    error_message = models.TextField(blank=True)
    results = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_sync_type_display()} for {self.user_connection} - {self.status}"


class CrossPlatformPlaylist(models.Model):
    """Playlists that sync across multiple platforms"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cross_platform_playlists')
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    
    # Source playlist (the "master" playlist)
    source_service = models.ForeignKey(ExternalServiceConfig, on_delete=models.CASCADE, related_name='source_playlists')
    source_playlist = models.ForeignKey(ExternalPlaylist, on_delete=models.CASCADE, related_name='cross_platform_copies')
    
    # Auto-sync settings
    auto_sync = models.BooleanField(default=True)
    sync_frequency = models.CharField(max_length=20, default='daily')  # hourly, daily, weekly
    
    # Status
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (Cross-Platform)"


class CrossPlatformPlaylistSync(models.Model):
    """Sync relationships between cross-platform playlists and target services"""
    cross_platform_playlist = models.ForeignKey(CrossPlatformPlaylist, on_delete=models.CASCADE, related_name='syncs')
    target_service = models.ForeignKey(ExternalServiceConfig, on_delete=models.CASCADE)
    target_playlist = models.ForeignKey(ExternalPlaylist, on_delete=models.CASCADE, null=True, blank=True)
    
    # Sync configuration
    is_enabled = models.BooleanField(default=True)
    sync_direction = models.CharField(max_length=20, default='one_way')  # one_way, two_way
    
    # Status
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_errors = models.JSONField(default=list)
    
    class Meta:
        unique_together = ('cross_platform_playlist', 'target_service')
    
    def __str__(self):
        return f"{self.cross_platform_playlist.name} -> {self.target_service.display_name}"
