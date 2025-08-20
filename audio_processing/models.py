from django.db import models
from django.contrib.auth.models import User


class AudioProcessingJob(models.Model):
    """Audio processing jobs for real-time analysis"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PROCESSING_TYPE_CHOICES = [
        ('spectrum_analysis', 'Spectrum Analysis'),
        ('beat_detection', 'Beat Detection'),
        ('mood_analysis', 'Mood Analysis'),
        ('visualization', 'Audio Visualization'),
        ('feature_extraction', 'Feature Extraction'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    processing_type = models.CharField(max_length=50, choices=PROCESSING_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Input
    audio_file = models.FileField(upload_to='processing/input/')
    parameters = models.JSONField(default=dict)
    
    # Output
    result_data = models.JSONField(default=dict)
    result_file = models.FileField(upload_to='processing/output/', blank=True, null=True)
    
    # Processing metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    # Error handling
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.processing_type} job for {self.user.username}"


class AudioVisualization(models.Model):
    """Real-time audio visualization data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100)  # WebSocket session identifier
    
    # Audio analysis data
    frequency_data = models.JSONField(help_text="Frequency spectrum data")
    amplitude_data = models.JSONField(help_text="Amplitude over time")
    beat_data = models.JSONField(help_text="Beat detection data")
    
    # Visualization parameters
    visualization_type = models.CharField(max_length=50, default='spectrum')
    color_scheme = models.CharField(max_length=50, default='default')
    sensitivity = models.FloatField(default=1.0)
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_id', '-timestamp']),
        ]

    def __str__(self):
        return f"Visualization for session {self.session_id}"


class AudioFeatures(models.Model):
    """Extracted audio features for music analysis"""
    # Link to track (if from streaming) or composition (if AI-generated)
    track_id = models.PositiveIntegerField(null=True, blank=True)
    composition_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Audio features
    tempo = models.FloatField()
    key = models.CharField(max_length=10)
    mode = models.IntegerField(help_text="0 for minor, 1 for major")
    
    # Spotify-style audio features
    acousticness = models.FloatField(default=0.0)
    danceability = models.FloatField(default=0.0)
    energy = models.FloatField(default=0.0)
    instrumentalness = models.FloatField(default=0.0)
    liveness = models.FloatField(default=0.0)
    loudness = models.FloatField(default=0.0)
    speechiness = models.FloatField(default=0.0)
    valence = models.FloatField(default=0.0)  # Musical positivity
    
    # Spectral features
    spectral_centroid = models.JSONField(default=list)
    mfcc = models.JSONField(default=list, help_text="Mel-frequency cepstral coefficients")
    chroma = models.JSONField(default=list)
    spectral_rolloff = models.JSONField(default=list)
    zero_crossing_rate = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['tempo']),
            models.Index(fields=['key']),
            models.Index(fields=['danceability']),
            models.Index(fields=['energy']),
        ]

    def __str__(self):
        return f"Features for track/composition {self.track_id or self.composition_id}"


class RealtimeSession(models.Model):
    """Active real-time audio processing sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    
    # Session state
    is_active = models.BooleanField(default=True)
    processing_type = models.CharField(max_length=50)
    
    # WebSocket connection info
    channel_name = models.CharField(max_length=100, blank=True)
    
    # Session metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-last_activity']),
            models.Index(fields=['is_active', '-last_activity']),
        ]

    def __str__(self):
        return f"Session {self.session_id} for {self.user.username}"
