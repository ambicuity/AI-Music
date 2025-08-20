import json
import uuid
import asyncio
from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import AudioProcessingJob, AudioVisualization, AudioFeatures, RealtimeSession
from .serializers import (
    AudioProcessingJobSerializer, AudioVisualizationSerializer,
    AudioFeaturesSerializer, RealtimeSessionSerializer
)
from .audio_analyzer import AudioAnalyzer  # We'll create this


class AudioProcessingJobViewSet(viewsets.ModelViewSet):
    """ViewSet for audio processing jobs"""
    serializer_class = AudioProcessingJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AudioProcessingJob.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        job = serializer.save(user=self.request.user)
        # In a real implementation, this would trigger async processing
        self._simulate_processing(job)

    def _simulate_processing(self, job):
        """Simulate audio processing (in reality, this would be async)"""
        # Update job status
        job.status = 'processing'
        job.save()
        
        # Simulate processing based on type
        if job.processing_type == 'spectrum_analysis':
            job.result_data = {
                'frequencies': [440, 880, 1320, 1760],  # Simulated frequency data
                'amplitudes': [0.8, 0.6, 0.4, 0.2],
                'dominant_frequency': 440
            }
        elif job.processing_type == 'beat_detection':
            job.result_data = {
                'bpm': 120,
                'beat_times': [0, 0.5, 1.0, 1.5, 2.0],  # Beat timestamps
                'confidence': 0.85
            }
        elif job.processing_type == 'mood_analysis':
            job.result_data = {
                'mood': 'happy',
                'valence': 0.7,
                'energy': 0.6,
                'confidence': 0.8
            }
        
        job.status = 'completed'
        job.save()

    @action(detail=False, methods=['post'])
    def batch_process(self, request):
        """Process multiple audio files"""
        files = request.data.getlist('files', [])
        processing_type = request.data.get('type', 'spectrum_analysis')
        
        jobs = []
        for file in files:
            job = AudioProcessingJob.objects.create(
                user=request.user,
                processing_type=processing_type,
                audio_file=file
            )
            self._simulate_processing(job)
            jobs.append(job)
        
        serializer = self.get_serializer(jobs, many=True)
        return Response(serializer.data)


class AudioVisualizationViewSet(viewsets.ModelViewSet):
    """ViewSet for audio visualizations"""
    serializer_class = AudioVisualizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AudioVisualization.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AudioFeaturesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for extracted audio features"""
    serializer_class = AudioFeaturesSerializer
    
    def get_queryset(self):
        return AudioFeatures.objects.all()

    @action(detail=False)
    def similar(self, request):
        """Find tracks with similar audio features"""
        track_id = request.query_params.get('track_id')
        if not track_id:
            return Response(
                {'error': 'track_id parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reference_features = AudioFeatures.objects.get(track_id=track_id)
        except AudioFeatures.DoesNotExist:
            return Response(
                {'error': 'Track features not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Simple similarity based on tempo and energy (in reality, would use ML)
        similar_features = AudioFeatures.objects.exclude(
            track_id=track_id
        ).filter(
            tempo__range=(reference_features.tempo - 20, reference_features.tempo + 20),
            energy__range=(reference_features.energy - 0.2, reference_features.energy + 0.2)
        )[:10]
        
        serializer = self.get_serializer(similar_features, many=True)
        return Response(serializer.data)


class RealtimeSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing real-time sessions"""
    serializer_class = RealtimeSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RealtimeSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        serializer.save(
            user=self.request.user,
            session_id=session_id
        )

    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """Start real-time audio processing for a session"""
        session = self.get_object()
        
        # Activate session
        session.is_active = True
        session.save()
        
        # Send initialization message to WebSocket
        channel_layer = get_channel_layer()
        if session.channel_name:
            async_to_sync(channel_layer.send)(session.channel_name, {
                'type': 'processing.start',
                'session_id': session.session_id,
                'processing_type': session.processing_type
            })
        
        return Response({
            'status': 'started',
            'session_id': session.session_id
        })

    @action(detail=True, methods=['post'])
    def stop_processing(self, request, pk=None):
        """Stop real-time audio processing for a session"""
        session = self.get_object()
        
        # Deactivate session
        session.is_active = False
        session.save()
        
        # Send stop message to WebSocket
        channel_layer = get_channel_layer()
        if session.channel_name:
            async_to_sync(channel_layer.send)(session.channel_name, {
                'type': 'processing.stop',
                'session_id': session.session_id
            })
        
        return Response({
            'status': 'stopped',
            'session_id': session.session_id
        })

    @action(detail=False)
    def active_sessions(self, request):
        """Get all active sessions for the user"""
        active = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(active, many=True)
        return Response(serializer.data)
