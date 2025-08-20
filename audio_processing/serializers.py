from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AudioProcessingJob, AudioVisualization, AudioFeatures, RealtimeSession


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class AudioProcessingJobSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    processing_time_formatted = serializers.SerializerMethodField()

    class Meta:
        model = AudioProcessingJob
        fields = [
            'id', 'user', 'processing_type', 'status', 'audio_file', 'parameters',
            'result_data', 'result_file', 'created_at', 'started_at', 'completed_at',
            'processing_time', 'processing_time_formatted', 'error_message'
        ]
        read_only_fields = [
            'user', 'status', 'result_data', 'result_file', 'started_at',
            'completed_at', 'processing_time', 'error_message'
        ]

    def get_processing_time_formatted(self, obj):
        if obj.processing_time:
            return f"{obj.processing_time:.2f}s"
        return None


class AudioVisualizationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AudioVisualization
        fields = [
            'id', 'user', 'session_id', 'frequency_data', 'amplitude_data',
            'beat_data', 'visualization_type', 'color_scheme', 'sensitivity',
            'timestamp'
        ]
        read_only_fields = ['user']


class AudioFeaturesSerializer(serializers.ModelSerializer):
    tempo_bpm = serializers.SerializerMethodField()
    key_formatted = serializers.SerializerMethodField()
    mode_name = serializers.SerializerMethodField()

    class Meta:
        model = AudioFeatures
        fields = [
            'id', 'track_id', 'composition_id', 'tempo', 'tempo_bpm', 'key', 
            'key_formatted', 'mode', 'mode_name', 'acousticness', 'danceability',
            'energy', 'instrumentalness', 'liveness', 'loudness', 'speechiness',
            'valence', 'spectral_centroid', 'mfcc', 'chroma', 'spectral_rolloff',
            'zero_crossing_rate', 'created_at'
        ]

    def get_tempo_bpm(self, obj):
        return f"{obj.tempo:.1f} BPM"

    def get_key_formatted(self, obj):
        return f"{obj.key} {'Major' if obj.mode == 1 else 'Minor'}"

    def get_mode_name(self, obj):
        return 'Major' if obj.mode == 1 else 'Minor'


class RealtimeSessionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = RealtimeSession
        fields = [
            'id', 'user', 'session_id', 'is_active', 'processing_type',
            'channel_name', 'created_at', 'last_activity', 'duration'
        ]
        read_only_fields = ['user', 'session_id', 'channel_name']

    def get_duration(self, obj):
        if obj.is_active:
            from django.utils import timezone
            duration = timezone.now() - obj.created_at
            return duration.total_seconds()
        return None