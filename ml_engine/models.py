from django.db import models
from django.contrib.auth.models import User
from composition.models import Genre
import json


class AIModel(models.Model):
    """AI models available for music generation"""
    MODEL_TYPES = [
        ('transformer', 'Transformer'),
        ('rnn', 'RNN/LSTM'),
        ('vae', 'Variational Autoencoder'),
        ('gan', 'Generative Adversarial Network'),
        ('diffusion', 'Diffusion Model'),
    ]
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=20, choices=MODEL_TYPES)
    version = models.CharField(max_length=20)
    description = models.TextField()
    
    # Model capabilities
    supported_genres = models.ManyToManyField(Genre, blank=True)
    max_duration = models.PositiveIntegerField(default=300, help_text="Maximum duration in seconds")
    sample_rate = models.PositiveIntegerField(default=44100)
    
    # Model parameters
    parameters = models.JSONField(default=dict, help_text="Model configuration parameters")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    training_completion = models.FloatField(default=100.0, help_text="Training completion percentage")
    
    # Performance metrics
    quality_score = models.FloatField(default=0.0, help_text="Subjective quality score (0-10)")
    generation_speed = models.FloatField(default=1.0, help_text="Generation speed multiplier")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'version')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} v{self.version}"


class MusicTheoryRule(models.Model):
    """Music theory rules for AI generation guidance"""
    RULE_TYPES = [
        ('harmony', 'Harmonic Rules'),
        ('melody', 'Melodic Rules'),
        ('rhythm', 'Rhythmic Rules'),
        ('form', 'Form and Structure'),
        ('voice_leading', 'Voice Leading'),
    ]
    
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    description = models.TextField()
    
    # Rule configuration
    parameters = models.JSONField(default=dict)
    weight = models.FloatField(default=1.0, help_text="Rule importance weight")
    
    # Applicable contexts
    genres = models.ManyToManyField(Genre, blank=True)
    key_signatures = models.JSONField(default=list, help_text="Applicable key signatures")
    time_signatures = models.JSONField(default=list, help_text="Applicable time signatures")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"


class GenerationRequest(models.Model):
    """AI music generation requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generation_requests')
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    
    # Generation parameters
    title = models.CharField(max_length=200, blank=True)
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True)
    duration = models.PositiveIntegerField(default=60)  # seconds
    tempo = models.PositiveIntegerField(default=120)  # BPM
    key_signature = models.CharField(max_length=10, default='C')
    
    # Advanced parameters
    creativity_level = models.FloatField(default=0.7, help_text="Creativity vs adherence to training (0-1)")
    mood = models.CharField(max_length=50, blank=True)
    instruments = models.JSONField(default=list)
    style_reference = models.CharField(max_length=200, blank=True, help_text="Style reference description")
    
    # Custom parameters
    custom_parameters = models.JSONField(default=dict)
    music_theory_rules = models.ManyToManyField(MusicTheoryRule, blank=True)
    
    # Status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.FloatField(default=0.0, help_text="Generation progress (0-100)")
    error_message = models.TextField(blank=True)
    
    # Output
    generated_composition = models.ForeignKey(
        'composition.MusicComposition', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='generation_request'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Generation request by {self.user.username} - {self.status}"


class TrainingDataset(models.Model):
    """Training datasets for AI models"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Dataset metadata
    total_tracks = models.PositiveIntegerField(default=0)
    total_duration = models.PositiveIntegerField(default=0, help_text="Total duration in seconds")
    genres = models.ManyToManyField(Genre)
    
    # Dataset format
    audio_format = models.CharField(max_length=20, default='wav')
    sample_rate = models.PositiveIntegerField(default=44100)
    bit_depth = models.PositiveIntegerField(default=16)
    
    # Data preprocessing
    preprocessing_config = models.JSONField(default=dict)
    
    # Status
    is_processed = models.BooleanField(default=False)
    processing_progress = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class ModelTrainingJob(models.Model):
    """AI model training jobs"""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('stopped', 'Stopped'),
    ]
    
    ai_model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='training_jobs')
    dataset = models.ForeignKey(TrainingDataset, on_delete=models.CASCADE)
    
    # Training configuration
    training_config = models.JSONField(default=dict)
    epochs = models.PositiveIntegerField(default=100)
    batch_size = models.PositiveIntegerField(default=32)
    learning_rate = models.FloatField(default=0.001)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    current_epoch = models.PositiveIntegerField(default=0)
    loss_history = models.JSONField(default=list)
    metrics = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Training {self.ai_model.name} - {self.status}"
