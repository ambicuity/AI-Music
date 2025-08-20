from django.db import models
from django.contrib.auth.models import User


class Artist(models.Model):
    """Music artists"""
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='artists/', blank=True, null=True)
    spotify_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Album(models.Model):
    """Music albums"""
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    cover_art = models.ImageField(upload_to='albums/', blank=True, null=True)
    release_date = models.DateField()
    spotify_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.artist.name}"


class Track(models.Model):
    """Individual music tracks for streaming"""
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, null=True, blank=True)
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    track_number = models.PositiveIntegerField(default=1)
    
    # Audio file (in real implementation, would use CDN/cloud storage)
    audio_file = models.FileField(upload_to='tracks/', blank=True, null=True)
    preview_url = models.URLField(blank=True, help_text="Preview URL for 30-second clips")
    
    # Metadata for discovery
    genre = models.CharField(max_length=100, blank=True)
    mood = models.CharField(max_length=100, blank=True)
    tempo = models.CharField(max_length=50, blank=True)
    key_signature = models.CharField(max_length=10, blank=True)
    
    # Streaming metrics
    play_count = models.PositiveBigIntegerField(default=0)  # BigInt for massive scale
    skip_count = models.PositiveBigIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    # External IDs
    spotify_id = models.CharField(max_length=100, blank=True, unique=True, null=True)
    isrc = models.CharField(max_length=20, blank=True, help_text="International Standard Recording Code")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['album', 'track_number']
        indexes = [
            models.Index(fields=['artist', '-play_count']),
            models.Index(fields=['genre', '-play_count']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.title} by {self.artist.name}"


class Playlist(models.Model):
    """User-created playlists"""
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    tracks = models.ManyToManyField(Track, through='PlaylistTrack')
    is_public = models.BooleanField(default=False)
    cover_image = models.ImageField(upload_to='playlists/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"{self.name} by {self.user.username}"


class PlaylistTrack(models.Model):
    """Through model for playlist tracks with ordering"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']
        unique_together = ('playlist', 'track')

    def __str__(self):
        return f"{self.track.title} in {self.playlist.name}"


class UserListening(models.Model):
    """User listening history for recommendations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)
    duration_played = models.PositiveIntegerField(help_text="Seconds played")
    completed = models.BooleanField(default=False)
    
    # Context for better recommendations
    playlist = models.ForeignKey(Playlist, on_delete=models.SET_NULL, null=True, blank=True)
    source = models.CharField(max_length=50, default='direct')  # playlist, search, recommendation, etc.

    class Meta:
        indexes = [
            models.Index(fields=['user', '-played_at']),
            models.Index(fields=['track', '-played_at']),
        ]

    def __str__(self):
        return f"{self.user.username} played {self.track.title}"
