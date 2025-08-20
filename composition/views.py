import json
import random
from django.shortcuts import render
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Genre, MusicComposition, CompositionLike
from .serializers import GenreSerializer, MusicCompositionSerializer, CompositionLikeSerializer


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for music genres"""
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class MusicCompositionViewSet(viewsets.ModelViewSet):
    """ViewSet for AI music compositions"""
    serializer_class = MusicCompositionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            # Show public compositions and user's own compositions
            return MusicComposition.objects.filter(
                models.Q(is_public=True) | models.Q(user=user)
            ).select_related('user', 'genre')
        return MusicComposition.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a new AI composition"""
        # Simulated AI generation parameters
        params = {
            'genre': request.data.get('genre', 'pop'),
            'tempo': request.data.get('tempo', 'moderate'),
            'key': request.data.get('key', 'C'),
            'duration': request.data.get('duration', 120),
            'mood': request.data.get('mood', 'happy'),
            'instruments': request.data.get('instruments', ['piano', 'guitar'])
        }
        
        # Simulate AI generation process
        title = f"AI Composition {random.randint(1000, 9999)}"
        
        # Create simulated MIDI data (in real implementation, this would be actual AI generation)
        midi_data = self._generate_simulated_midi(params)
        
        # Get or create genre
        genre_name = params['genre']
        genre, _ = Genre.objects.get_or_create(name=genre_name)
        
        composition = MusicComposition.objects.create(
            title=title,
            user=request.user,
            genre=genre,
            tempo=params['tempo'],
            key_signature=params['key'],
            duration=params['duration'],
            ai_model_version='v1.0',
            generation_parameters=params,
            midi_data=midi_data
        )
        
        serializer = self.get_serializer(composition)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike a composition"""
        composition = self.get_object()
        like, created = CompositionLike.objects.get_or_create(
            user=request.user,
            composition=composition
        )
        
        if not created:
            like.delete()
            composition.like_count = max(0, composition.like_count - 1)
            liked = False
        else:
            composition.like_count += 1
            liked = True
        
        composition.save()
        
        return Response({
            'liked': liked,
            'like_count': composition.like_count
        })

    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        """Increment play count"""
        composition = self.get_object()
        composition.play_count += 1
        composition.save()
        
        return Response({
            'play_count': composition.play_count
        })

    def _generate_simulated_midi(self, params):
        """Generate simulated MIDI data based on parameters"""
        # This is a simplified simulation - in reality, this would use an AI model
        notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        midi_sequence = []
        
        for i in range(int(params['duration'] / 4)):  # One note every 4 seconds
            note = random.choice(notes)
            octave = random.randint(3, 6)
            velocity = random.randint(60, 100)
            
            midi_sequence.append({
                'time': i * 4,
                'note': f"{note}{octave}",
                'velocity': velocity,
                'duration': random.uniform(1, 3)
            })
        
        return json.dumps(midi_sequence)
