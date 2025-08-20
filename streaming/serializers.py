from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Artist, Album, Track, Playlist, PlaylistTrack, UserListening


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['id', 'name', 'bio', 'image', 'created_at']


class AlbumSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    
    class Meta:
        model = Album
        fields = ['id', 'title', 'artist', 'cover_art', 'release_date', 'created_at']


class TrackSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(read_only=True)
    album = AlbumSerializer(read_only=True)
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'album', 'duration', 'duration_formatted',
            'track_number', 'preview_url', 'genre', 'mood', 'tempo', 
            'key_signature', 'play_count', 'like_count', 'created_at'
        ]

    def get_duration_formatted(self, obj):
        """Format duration as MM:SS"""
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f"{minutes}:{seconds:02d}"


class PlaylistTrackSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)

    class Meta:
        model = PlaylistTrack
        fields = ['track', 'position', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    tracks_detail = PlaylistTrackSerializer(
        source='playlisttrack_set', 
        many=True, 
        read_only=True
    )
    track_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'user', 'description', 'is_public', 'cover_image',
            'tracks_detail', 'track_count', 'total_duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user']

    def get_track_count(self, obj):
        return obj.tracks.count()

    def get_total_duration(self, obj):
        total = sum(track.duration for track in obj.tracks.all())
        minutes = total // 60
        seconds = total % 60
        return f"{minutes}:{seconds:02d}"


class UserListeningSerializer(serializers.ModelSerializer):
    track = TrackSerializer(read_only=True)
    playlist = PlaylistSerializer(read_only=True)
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = UserListening
        fields = [
            'id', 'track', 'playlist', 'played_at', 'duration_played',
            'duration_formatted', 'completed', 'source'
        ]

    def get_duration_formatted(self, obj):
        """Format duration as MM:SS"""
        minutes = obj.duration_played // 60
        seconds = obj.duration_played % 60
        return f"{minutes}:{seconds:02d}"