from django.shortcuts import render
from django.db import models
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Artist, Album, Track, Playlist, PlaylistTrack, UserListening
from .serializers import (
    ArtistSerializer, AlbumSerializer, TrackSerializer, 
    PlaylistSerializer, UserListeningSerializer
)


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for artists"""
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'bio']


class AlbumViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for albums"""
    queryset = Album.objects.select_related('artist').all()
    serializer_class = AlbumSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'artist__name']
    filterset_fields = ['artist']


class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for tracks with streaming capabilities"""
    queryset = Track.objects.select_related('artist', 'album').all()
    serializer_class = TrackSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'artist__name', 'album__title']
    filterset_fields = ['artist', 'album', 'genre']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def play(self, request, pk=None):
        """Record a play event and return streaming URL"""
        track = self.get_object()
        
        # Record listening event
        UserListening.objects.create(
            user=request.user,
            track=track,
            source='direct'
        )
        
        # Increment play count (in production, this might be batched)
        track.play_count += 1
        track.save()
        
        # Return streaming information (in production, this would be a CDN URL)
        return Response({
            'stream_url': track.audio_file.url if track.audio_file else None,
            'preview_url': track.preview_url,
            'play_count': track.play_count
        })

    @action(detail=False)
    def trending(self, request):
        """Get trending tracks based on recent play counts"""
        trending_tracks = Track.objects.order_by('-play_count')[:50]
        serializer = self.get_serializer(trending_tracks, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def recommendations(self, request):
        """Get personalized recommendations (simplified)"""
        if not request.user.is_authenticated:
            # Return popular tracks for anonymous users
            popular_tracks = Track.objects.order_by('-play_count')[:20]
        else:
            # Simple recommendation based on user's listening history
            user_genres = UserListening.objects.filter(
                user=request.user
            ).values_list('track__genre', flat=True).distinct()
            
            if user_genres:
                recommended_tracks = Track.objects.filter(
                    genre__in=user_genres
                ).exclude(
                    id__in=UserListening.objects.filter(
                        user=request.user
                    ).values_list('track_id', flat=True)
                ).order_by('-play_count')[:20]
            else:
                recommended_tracks = Track.objects.order_by('-play_count')[:20]
            
            popular_tracks = recommended_tracks
        
        serializer = self.get_serializer(popular_tracks, many=True)
        return Response(serializer.data)


class PlaylistViewSet(viewsets.ModelViewSet):
    """ViewSet for user playlists"""
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if self.action == 'list':
            # Show public playlists and user's own playlists
            return Playlist.objects.filter(
                models.Q(is_public=True) | models.Q(user=user)
            ).prefetch_related('tracks')
        return Playlist.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_track(self, request, pk=None):
        """Add a track to the playlist"""
        playlist = self.get_object()
        track_id = request.data.get('track_id')
        
        try:
            track = Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return Response(
                {'error': 'Track not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get the next position
        last_track = PlaylistTrack.objects.filter(
            playlist=playlist
        ).order_by('-position').first()
        
        position = (last_track.position + 1) if last_track else 1
        
        playlist_track, created = PlaylistTrack.objects.get_or_create(
            playlist=playlist,
            track=track,
            defaults={'position': position}
        )
        
        if created:
            return Response({'message': 'Track added to playlist'})
        else:
            return Response(
                {'error': 'Track already in playlist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def remove_track(self, request, pk=None):
        """Remove a track from the playlist"""
        playlist = self.get_object()
        track_id = request.data.get('track_id')
        
        try:
            playlist_track = PlaylistTrack.objects.get(
                playlist=playlist, 
                track_id=track_id
            )
            playlist_track.delete()
            return Response({'message': 'Track removed from playlist'})
        except PlaylistTrack.DoesNotExist:
            return Response(
                {'error': 'Track not in playlist'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        """Play a playlist and record listening events"""
        playlist = self.get_object()
        tracks = playlist.tracks.all()
        
        # Record playlist play
        for track in tracks[:10]:  # Limit to first 10 tracks for demo
            UserListening.objects.create(
                user=request.user,
                track=track,
                playlist=playlist,
                source='playlist'
            )
        
        serializer = self.get_serializer(playlist)
        return Response(serializer.data)


class UserListeningViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user listening history"""
    serializer_class = UserListeningSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserListening.objects.filter(
            user=self.request.user
        ).select_related('track__artist', 'track__album')

    @action(detail=False)
    def stats(self, request):
        """Get user listening statistics"""
        user_listening = self.get_queryset()
        
        total_plays = user_listening.count()
        total_duration = user_listening.aggregate(
            total=models.Sum('duration_played')
        )['total'] or 0
        
        # Top artists
        top_artists = user_listening.values(
            'track__artist__name'
        ).annotate(
            play_count=models.Count('id')
        ).order_by('-play_count')[:10]
        
        # Top tracks
        top_tracks = user_listening.values(
            'track__title', 'track__artist__name'
        ).annotate(
            play_count=models.Count('id')
        ).order_by('-play_count')[:10]
        
        return Response({
            'total_plays': total_plays,
            'total_duration': total_duration,
            'top_artists': list(top_artists),
            'top_tracks': list(top_tracks)
        })
