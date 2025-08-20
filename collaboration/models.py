from django.db import models
from django.contrib.auth.models import User
from composition.models import MusicComposition, Genre
from django.utils import timezone
import json


class CollaborativeSession(models.Model):
    """Real-time collaborative composition sessions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    PERMISSION_LEVELS = [
        ('view', 'View Only'),
        ('comment', 'Comment Only'),  
        ('edit', 'Edit'),
        ('admin', 'Admin'),
    ]
    
    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sessions')
    
    # Composition details
    base_composition = models.ForeignKey(MusicComposition, on_delete=models.SET_NULL, null=True, blank=True)
    target_genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    target_duration = models.PositiveIntegerField(default=120, help_text="Target duration in seconds")
    target_tempo = models.PositiveIntegerField(default=120, help_text="Target BPM")
    key_signature = models.CharField(max_length=10, default='C')
    
    # Session settings
    max_participants = models.PositiveIntegerField(default=10)
    is_public = models.BooleanField(default=False)
    requires_approval = models.BooleanField(default=True)
    allow_ai_suggestions = models.BooleanField(default=True)
    
    # Real-time composition data
    composition_data = models.JSONField(default=dict, help_text="Current state of the composition")
    version = models.PositiveIntegerField(default=1)
    
    # Session management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    session_token = models.CharField(max_length=100, unique=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session_token']),
            models.Index(fields=['status', '-last_activity']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.creator.username}"


class SessionParticipant(models.Model):
    """Participants in collaborative sessions"""
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission_level = models.CharField(max_length=20, choices=CollaborativeSession.PERMISSION_LEVELS, default='edit')
    
    # Participation info
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    
    # Contribution tracking
    contributions_count = models.PositiveIntegerField(default=0)
    notes_added = models.PositiveIntegerField(default=0)
    edits_made = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('session', 'user')
        indexes = [
            models.Index(fields=['session', 'is_online']),
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.session.title}"


class CompositionChange(models.Model):
    """Track individual changes made to the composition"""
    CHANGE_TYPES = [
        ('note_add', 'Note Added'),
        ('note_remove', 'Note Removed'),
        ('note_edit', 'Note Edited'),
        ('chord_add', 'Chord Added'),
        ('chord_remove', 'Chord Removed'),
        ('chord_edit', 'Chord Edited'),
        ('tempo_change', 'Tempo Changed'),
        ('key_change', 'Key Changed'),
        ('instrument_add', 'Instrument Added'),
        ('instrument_remove', 'Instrument Removed'),
        ('effect_add', 'Effect Added'),
        ('effect_remove', 'Effect Removed'),
        ('structure_change', 'Structure Changed'),
    ]
    
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='changes')
    participant = models.ForeignKey(SessionParticipant, on_delete=models.CASCADE)
    
    # Change details
    change_type = models.CharField(max_length=30, choices=CHANGE_TYPES)
    change_data = models.JSONField(help_text="Details of what was changed")
    previous_data = models.JSONField(null=True, blank=True, help_text="Previous state for undo")
    
    # Context
    measure = models.PositiveIntegerField(null=True, blank=True)
    beat = models.FloatField(null=True, blank=True)
    track_name = models.CharField(max_length=100, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    is_reverted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', '-timestamp']),
            models.Index(fields=['participant', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_change_type_display()} by {self.participant.user.username}"


class SessionComment(models.Model):
    """Comments and discussions within collaborative sessions"""
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='comments')
    participant = models.ForeignKey(SessionParticipant, on_delete=models.CASCADE)
    
    # Comment content
    content = models.TextField()
    
    # Context - what part of composition this relates to
    measure = models.PositiveIntegerField(null=True, blank=True)
    beat = models.FloatField(null=True, blank=True)
    track_name = models.CharField(max_length=100, blank=True)
    
    # Threading
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.participant.user.username}: {self.content[:50]}..."


class SessionVersion(models.Model):
    """Saved versions/snapshots of collaborative compositions"""
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='versions')
    created_by = models.ForeignKey(SessionParticipant, on_delete=models.CASCADE)
    
    # Version info
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # Composition snapshot
    composition_data = models.JSONField()
    audio_preview = models.FileField(upload_to='collaboration/previews/', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('session', 'version_number')
        ordering = ['-version_number']
    
    def __str__(self):
        return f"Version {self.version_number} of {self.session.title}"


class AICollaborationSuggestion(models.Model):
    """AI-generated suggestions for collaborative compositions"""
    SUGGESTION_TYPES = [
        ('harmony', 'Harmonic Improvement'),
        ('melody', 'Melodic Enhancement'),
        ('rhythm', 'Rhythmic Variation'),
        ('structure', 'Structural Change'),
        ('instrumentation', 'Instrumentation Suggestion'),
        ('style', 'Style Enhancement'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('implemented', 'Implemented'),
    ]
    
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='ai_suggestions')
    suggestion_type = models.CharField(max_length=30, choices=SUGGESTION_TYPES)
    
    # Suggestion details
    title = models.CharField(max_length=200)
    description = models.TextField()
    suggested_changes = models.JSONField()
    confidence_score = models.FloatField(default=0.5, help_text="AI confidence in suggestion (0-1)")
    
    # Context
    applies_to_measure = models.PositiveIntegerField(null=True, blank=True)
    applies_to_track = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(SessionParticipant, on_delete=models.SET_NULL, null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-confidence_score', '-created_at']
    
    def __str__(self):
        return f"{self.get_suggestion_type_display()}: {self.title}"


class SessionInvitation(models.Model):
    """Invitations to join collaborative sessions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invitations')
    
    # Invitation details
    message = models.TextField(blank=True)
    permission_level = models.CharField(max_length=20, choices=CollaborativeSession.PERMISSION_LEVELS, default='edit')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    invitation_token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('session', 'invited_user')
        indexes = [
            models.Index(fields=['invitation_token']),
            models.Index(fields=['invited_user', 'status']),
        ]
    
    def __str__(self):
        return f"Invitation to {self.invited_user.username} for {self.session.title}"


class RealTimeEvent(models.Model):
    """Real-time events for WebSocket broadcasting"""
    EVENT_TYPES = [
        ('user_joined', 'User Joined'),
        ('user_left', 'User Left'),
        ('composition_changed', 'Composition Changed'),
        ('comment_added', 'Comment Added'),
        ('suggestion_made', 'AI Suggestion Made'),
        ('version_saved', 'Version Saved'),
        ('playback_sync', 'Playback Sync'),
    ]
    
    session = models.ForeignKey(CollaborativeSession, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Event data
    event_data = models.JSONField(default=dict)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', '-timestamp']),
            models.Index(fields=['processed', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} in {self.session.title}"
