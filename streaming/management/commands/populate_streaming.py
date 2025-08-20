from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from streaming.models import Artist, Album, Track, Playlist, PlaylistTrack
import random
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Populate the database with sample streaming data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample streaming data...')
        
        # Create artists
        artists_data = [
            {'name': 'The Digital Dreamers', 'bio': 'Electronic music collective from the future'},
            {'name': 'Sarah Jazz', 'bio': 'Contemporary jazz pianist and composer'},
            {'name': 'Rock Mountain', 'bio': 'High-energy rock band from Colorado'},
            {'name': 'Classical Ensemble', 'bio': 'Traditional classical music group'},
            {'name': 'Hip-Hop Heroes', 'bio': 'Urban music pioneers'},
            {'name': 'Blues Brothers Revival', 'bio': 'Modern blues with classic soul'},
            {'name': 'Country Roads', 'bio': 'Authentic country music from Nashville'},
            {'name': 'Pop Stars United', 'bio': 'Catchy pop melodies for the masses'},
        ]
        
        artists = []
        for artist_data in artists_data:
            artist, created = Artist.objects.get_or_create(
                name=artist_data['name'],
                defaults={'bio': artist_data['bio']}
            )
            artists.append(artist)
            if created:
                self.stdout.write(f'Created artist: {artist.name}')
        
        # Create albums
        album_titles = [
            'Digital Dreams', 'Jazz Nights', 'Rock Solid', 'Classical Movements',
            'Street Beats', 'Blue Mood', 'Country Life', 'Pop Perfection',
            'Electronic Voyage', 'Smooth Jazz', 'Hard Rock', 'Symphony No. 1'
        ]
        
        albums = []
        for i, title in enumerate(album_titles):
            if Album.objects.filter(title=title).exists():
                albums.extend(Album.objects.filter(title=title))
                continue
                
            album = Album.objects.create(
                title=title,
                artist=artists[i % len(artists)],
                release_date=date.today() - timedelta(days=random.randint(30, 3650))
            )
            albums.append(album)
            self.stdout.write(f'Created album: {album.title}')
        
        # Create tracks
        track_names = [
            'Midnight Glow', 'Sunrise Melody', 'Electric Storm', 'Gentle Breeze',
            'Urban Jungle', 'Desert Sunset', 'Ocean Deep', 'Mountain High',
            'Neon Lights', 'Starry Night', 'Dancing Shadows', 'Crystal Clear',
            'Burning Fire', 'Flowing River', 'Soaring Eagle', 'Peaceful Valley',
            'Thunder Clap', 'Whispered Dreams', 'Golden Hour', 'Silver Moon'
        ]
        
        genres = ['Pop', 'Rock', 'Jazz', 'Electronic', 'Hip-Hop', 'Blues', 'Country', 'Classical']
        moods = ['happy', 'sad', 'energetic', 'calm', 'romantic', 'aggressive', 'peaceful']
        
        tracks = []
        for i, track_name in enumerate(track_names):
            if Track.objects.filter(title=track_name).exists():
                tracks.extend(Track.objects.filter(title=track_name))
                continue
            
            album = albums[i % len(albums)]
            track = Track.objects.create(
                title=track_name,
                artist=album.artist,
                album=album,
                duration=random.randint(120, 300),  # 2-5 minutes
                track_number=i % 12 + 1,
                genre=random.choice(genres),
                mood=random.choice(moods),
                tempo=f"{random.randint(80, 160)} BPM",
                key_signature=random.choice(['C', 'G', 'D', 'A', 'E', 'F', 'Bb']),
                play_count=random.randint(100, 100000),
                skip_count=random.randint(10, 10000),
                like_count=random.randint(5, 5000),
                preview_url=f"https://preview.example.com/{track_name.lower().replace(' ', '-')}"
            )
            tracks.append(track)
            self.stdout.write(f'Created track: {track.title}')
        
        # Create playlists
        users = User.objects.all()
        if not users:
            # Create a test user if none exist
            user = User.objects.create_user('musiclover', 'music@example.com', 'password123')
            users = [user]
        
        playlist_names = [
            'My Favorites', 'Workout Mix', 'Chill Vibes', 'Party Time',
            'Study Music', 'Road Trip', 'Romantic Evening', 'Morning Motivation'
        ]
        
        for playlist_name in playlist_names:
            if Playlist.objects.filter(name=playlist_name).exists():
                continue
                
            playlist = Playlist.objects.create(
                name=playlist_name,
                user=random.choice(users),
                description=f'A curated playlist of {playlist_name.lower()}',
                is_public=random.choice([True, False])
            )
            
            # Add random tracks to playlist
            selected_tracks = random.sample(tracks, min(random.randint(5, 15), len(tracks)))
            for position, track in enumerate(selected_tracks, 1):
                PlaylistTrack.objects.create(
                    playlist=playlist,
                    track=track,
                    position=position
                )
            
            self.stdout.write(f'Created playlist: {playlist.name} with {len(selected_tracks)} tracks')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated streaming data!')
        )