"""
External Music Service Clients

This module provides clients for integrating with external music services
like Spotify, Apple Music, etc.
"""

import requests
import json
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import base64
from .models import ExternalServiceConfig, UserServiceConnection, ExternalTrack, ExternalPlaylist


class BaseServiceClient:
    """Base class for external service clients"""
    
    def __init__(self, service_config: ExternalServiceConfig, user_connection: UserServiceConnection = None):
        self.service_config = service_config
        self.user_connection = user_connection
        self.base_url = service_config.api_base_url
    
    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Music-Platform/1.0'
        }
        
        if self.user_connection and self.user_connection.access_token:
            headers['Authorization'] = f'Bearer {self.user_connection.access_token}'
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make an API request with error handling"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired"""
        if not self.user_connection or not self.user_connection.expires_at:
            return True
        
        return timezone.now() >= self.user_connection.expires_at
    
    def refresh_token(self) -> bool:
        """Refresh the access token if possible"""
        # Override in subclasses
        return False


class SpotifyClient(BaseServiceClient):
    """Spotify API client"""
    
    def __init__(self, service_config: ExternalServiceConfig, user_connection: UserServiceConnection = None):
        super().__init__(service_config, user_connection)
        self.auth_url = "https://accounts.spotify.com/api/token"
    
    def refresh_token(self) -> bool:
        """Refresh Spotify access token"""
        if not self.user_connection or not self.user_connection.refresh_token:
            return False
        
        try:
            # Prepare credentials
            credentials = f"{self.service_config.client_id}:{self.service_config.client_secret}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials_b64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.user_connection.refresh_token
            }
            
            response = requests.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Update user connection
            self.user_connection.access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                self.user_connection.refresh_token = token_data['refresh_token']
            
            expires_in = token_data.get('expires_in', 3600)
            self.user_connection.expires_at = timezone.now() + timedelta(seconds=expires_in)
            self.user_connection.save()
            
            return True
            
        except Exception:
            return False
    
    def search_tracks(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for tracks on Spotify"""
        try:
            if self.is_token_expired():
                self.refresh_token()
            
            params = {
                'q': query,
                'type': 'track',
                'limit': limit
            }
            
            response = self._make_request('GET', '/v1/search', params=params)
            
            tracks = []
            for item in response.get('tracks', {}).get('items', []):
                track = {
                    'external_id': item['id'],
                    'title': item['name'],
                    'artist': ', '.join([artist['name'] for artist in item['artists']]),
                    'album': item['album']['name'],
                    'duration_ms': item.get('duration_ms'),
                    'popularity': item.get('popularity'),
                    'external_url': item['external_urls'].get('spotify'),
                    'preview_url': item.get('preview_url'),
                    'artwork_url': item['album']['images'][0]['url'] if item['album']['images'] else None,
                    'release_date': item['album'].get('release_date')
                }
                tracks.append(track)
            
            return tracks
            
        except Exception as e:
            raise Exception(f"Spotify search failed: {str(e)}")
    
    def get_track_features(self, track_id: str) -> Dict:
        """Get audio features for a track"""
        try:
            if self.is_token_expired():
                self.refresh_token()
            
            response = self._make_request('GET', f'/v1/audio-features/{track_id}')
            
            return {
                'acousticness': response.get('acousticness'),
                'danceability': response.get('danceability'),
                'energy': response.get('energy'),
                'instrumentalness': response.get('instrumentalness'),
                'liveness': response.get('liveness'),
                'loudness': response.get('loudness'),
                'speechiness': response.get('speechiness'),
                'valence': response.get('valence'),
                'tempo': response.get('tempo'),
                'key': response.get('key'),
                'mode': response.get('mode'),
                'time_signature': response.get('time_signature')
            }
            
        except Exception as e:
            raise Exception(f"Failed to get track features: {str(e)}")
    
    def get_user_playlists(self) -> List[Dict]:
        """Get user's playlists"""
        try:
            if self.is_token_expired():
                self.refresh_token()
            
            response = self._make_request('GET', '/v1/me/playlists')
            
            playlists = []
            for item in response.get('items', []):
                playlist = {
                    'external_id': item['id'],
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'is_public': item.get('public', False),
                    'track_count': item['tracks']['total'],
                    'followers_count': item.get('followers', {}).get('total', 0),
                    'external_url': item['external_urls'].get('spotify'),
                    'image_url': item['images'][0]['url'] if item['images'] else None
                }
                playlists.append(playlist)
            
            return playlists
            
        except Exception as e:
            raise Exception(f"Failed to get playlists: {str(e)}")
    
    def get_recommendations(self, seed_tracks: List[str] = None, seed_artists: List[str] = None, 
                          seed_genres: List[str] = None, limit: int = 20, **audio_features) -> List[Dict]:
        """Get recommendations from Spotify"""
        try:
            if self.is_token_expired():
                self.refresh_token()
            
            params = {'limit': limit}
            
            if seed_tracks:
                params['seed_tracks'] = ','.join(seed_tracks[:5])  # Max 5 seeds
            if seed_artists:
                params['seed_artists'] = ','.join(seed_artists[:5])
            if seed_genres:
                params['seed_genres'] = ','.join(seed_genres[:5])
            
            # Add audio feature targets
            for feature, value in audio_features.items():
                if feature in ['target_acousticness', 'target_danceability', 'target_energy',
                              'target_valence', 'target_tempo']:
                    params[feature] = value
            
            response = self._make_request('GET', '/v1/recommendations', params=params)
            
            recommendations = []
            for item in response.get('tracks', []):
                track = {
                    'external_id': item['id'],
                    'title': item['name'],
                    'artist': ', '.join([artist['name'] for artist in item['artists']]),
                    'album': item['album']['name'],
                    'external_url': item['external_urls'].get('spotify'),
                    'preview_url': item.get('preview_url'),
                    'popularity': item.get('popularity')
                }
                recommendations.append(track)
            
            return recommendations
            
        except Exception as e:
            raise Exception(f"Failed to get recommendations: {str(e)}")
    
    def create_playlist(self, name: str, description: str = '', public: bool = True) -> Dict:
        """Create a new playlist"""
        try:
            if self.is_token_expired():
                self.refresh_token()
            
            # Get user ID first
            user_response = self._make_request('GET', '/v1/me')
            user_id = user_response['id']
            
            data = {
                'name': name,
                'description': description,
                'public': public
            }
            
            response = self._make_request('POST', f'/v1/users/{user_id}/playlists', data=data)
            
            return {
                'external_id': response['id'],
                'name': response['name'],
                'external_url': response['external_urls'].get('spotify'),
                'snapshot_id': response.get('snapshot_id')
            }
            
        except Exception as e:
            raise Exception(f"Failed to create playlist: {str(e)}")


class AppleMusicClient(BaseServiceClient):
    """Apple Music API client"""
    
    def __init__(self, service_config: ExternalServiceConfig, user_connection: UserServiceConnection = None):
        super().__init__(service_config, user_connection)
        # Apple Music uses different authentication (JWT tokens)
    
    def search_tracks(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for tracks on Apple Music"""
        # Implementation for Apple Music API
        # Note: This would require Apple Music API setup
        return []
    
    def get_recommendations(self, **kwargs) -> List[Dict]:
        """Get recommendations from Apple Music"""
        # Implementation for Apple Music recommendations
        return []


class ServiceClientFactory:
    """Factory for creating service clients"""
    
    CLIENT_CLASSES = {
        'spotify': SpotifyClient,
        'apple_music': AppleMusicClient,
    }
    
    @classmethod
    def create_client(cls, service_name: str, user_connection: UserServiceConnection = None) -> BaseServiceClient:
        """Create a client for the specified service"""
        try:
            service_config = ExternalServiceConfig.objects.get(name=service_name, is_active=True)
            client_class = cls.CLIENT_CLASSES.get(service_name)
            
            if not client_class:
                raise ValueError(f"No client available for service: {service_name}")
            
            return client_class(service_config, user_connection)
            
        except ExternalServiceConfig.DoesNotExist:
            raise ValueError(f"Service not configured: {service_name}")


class RecommendationAggregator:
    """Aggregate recommendations from multiple services"""
    
    def __init__(self, user):
        self.user = user
        self.user_connections = UserServiceConnection.objects.filter(
            user=user,
            is_active=True
        ).select_related('service')
    
    def get_cross_platform_recommendations(self, limit: int = 50) -> List[Dict]:
        """Get recommendations from all connected services"""
        all_recommendations = []
        
        for connection in self.user_connections:
            try:
                client = ServiceClientFactory.create_client(
                    connection.service.name,
                    connection
                )
                
                if hasattr(client, 'get_recommendations'):
                    recommendations = client.get_recommendations(limit=limit//len(self.user_connections))
                    
                    # Add service info to each recommendation
                    for rec in recommendations:
                        rec['source_service'] = connection.service.name
                        rec['source_service_display'] = connection.service.display_name
                    
                    all_recommendations.extend(recommendations)
                    
            except Exception as e:
                # Log error but continue with other services
                print(f"Failed to get recommendations from {connection.service.name}: {e}")
                continue
        
        # Remove duplicates based on title and artist
        seen = set()
        unique_recommendations = []
        
        for rec in all_recommendations:
            key = (rec.get('title', '').lower(), rec.get('artist', '').lower())
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:limit]
    
    def sync_user_data(self, sync_type: str = 'playlists'):
        """Sync user data from all connected services"""
        for connection in self.user_connections:
            try:
                client = ServiceClientFactory.create_client(
                    connection.service.name,
                    connection
                )
                
                if sync_type == 'playlists' and hasattr(client, 'get_user_playlists'):
                    playlists = client.get_user_playlists()
                    self._sync_playlists(connection, playlists)
                
                connection.last_sync = timezone.now()
                connection.save()
                
            except Exception as e:
                print(f"Failed to sync {sync_type} from {connection.service.name}: {e}")
                continue
    
    def _sync_playlists(self, connection: UserServiceConnection, playlists: List[Dict]):
        """Sync playlists from external service"""
        for playlist_data in playlists:
            playlist, created = ExternalPlaylist.objects.get_or_create(
                service=connection.service,
                external_id=playlist_data['external_id'],
                defaults={
                    'user_connection': connection,
                    'name': playlist_data['name'],
                    'description': playlist_data.get('description', ''),
                    'is_public': playlist_data.get('is_public', True),
                    'track_count': playlist_data.get('track_count', 0),
                    'followers_count': playlist_data.get('followers_count', 0),
                    'external_url': playlist_data.get('external_url', ''),
                    'image_url': playlist_data.get('image_url', ''),
                    'last_synced': timezone.now(),
                    'is_synced': True
                }
            )
            
            if not created:
                # Update existing playlist
                playlist.name = playlist_data['name']
                playlist.description = playlist_data.get('description', '')
                playlist.track_count = playlist_data.get('track_count', 0)
                playlist.last_synced = timezone.now()
                playlist.save()