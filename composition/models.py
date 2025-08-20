from django.db import models
from django.contrib.auth.models import User


class Genre(models.Model):
    """Music genres for categorization"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MusicComposition(models.Model):
    """AI-generated music compositions"""
    TEMPO_CHOICES = [
        ('slow', 'Slow (60-90 BPM)'),
        ('moderate', 'Moderate (90-120 BPM)'),
        ('fast', 'Fast (120-160 BPM)'),
        ('very_fast', 'Very Fast (160+ BPM)'),
    ]

    KEY_CHOICES = [
        ('C', 'C Major'), ('Am', 'A Minor'),
        ('G', 'G Major'), ('Em', 'E Minor'),
        ('D', 'D Major'), ('Bm', 'B Minor'),
        ('A', 'A Major'), ('F#m', 'F# Minor'),
        ('E', 'E Major'), ('C#m', 'C# Minor'),
        ('B', 'B Major'), ('G#m', 'G# Minor'),
        ('F#', 'F# Major'), ('D#m', 'D# Minor'),
        ('F', 'F Major'), ('Dm', 'D Minor'),
        ('Bb', 'Bb Major'), ('Gm', 'G Minor'),
        ('Eb', 'Eb Major'), ('Cm', 'C Minor'),
        ('Ab', 'Ab Major'), ('Fm', 'F Minor'),
        ('Db', 'Db Major'), ('Bbm', 'Bb Minor'),
        ('Gb', 'Gb Major'), ('Ebm', 'Eb Minor'),
    ]

    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    tempo = models.CharField(max_length=20, choices=TEMPO_CHOICES, default='moderate')
    key_signature = models.CharField(max_length=10, choices=KEY_CHOICES, default='C')
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    
    # AI generation parameters
    ai_model_version = models.CharField(max_length=50, default='v1.0')
    generation_parameters = models.JSONField(default=dict, help_text="AI model parameters used")
    
    # Generated content (simulated)
    midi_data = models.TextField(blank=True, help_text="MIDI representation")
    audio_file = models.FileField(upload_to='compositions/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    play_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['genre', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class CompositionLike(models.Model):
    """User likes for compositions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    composition = models.ForeignKey(MusicComposition, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'composition')

    def __str__(self):
        return f"{self.user.username} likes {self.composition.title}"
