from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from composition.models import Genre, MusicComposition
import random
import json


class Command(BaseCommand):
    help = 'Populate the database with sample music composition data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample composition data...')
        
        # Create genres
        genres_data = [
            {'name': 'Pop', 'description': 'Popular music with catchy melodies'},
            {'name': 'Rock', 'description': 'Electric guitar-driven music'},
            {'name': 'Jazz', 'description': 'Improvisational and complex harmonies'},
            {'name': 'Classical', 'description': 'Traditional orchestral music'},
            {'name': 'Electronic', 'description': 'Synthesized and digital music'},
            {'name': 'Hip-Hop', 'description': 'Rhythmic spoken lyrics with beats'},
            {'name': 'Blues', 'description': 'Soulful music with blue notes'},
            {'name': 'Country', 'description': 'American rural folk music'},
        ]
        
        for genre_data in genres_data:
            genre, created = Genre.objects.get_or_create(
                name=genre_data['name'],
                defaults={'description': genre_data['description']}
            )
            if created:
                self.stdout.write(f'Created genre: {genre.name}')
        
        # Create some compositions
        users = User.objects.all()
        if not users:
            # Create a test user if none exist
            user = User.objects.create_user('testuser', 'test@example.com', 'password123')
            users = [user]
        
        genres = Genre.objects.all()
        
        composition_titles = [
            'Midnight Dreams', 'Digital Sunrise', 'Ocean Waves', 'City Lights',
            'Forest Whispers', 'Neon Nights', 'Gentle Rain', 'Thunder Storm',
            'Peaceful Meadow', 'Mountain Echo', 'Desert Wind', 'Northern Lights',
            'Dancing Flames', 'Frozen Lake', 'Blooming Spring', 'Autumn Leaves'
        ]
        
        tempos = ['slow', 'moderate', 'fast', 'very_fast']
        keys = ['C', 'G', 'D', 'A', 'E', 'F', 'Bb', 'Eb', 'Am', 'Em', 'Dm', 'Gm']
        
        for i, title in enumerate(composition_titles):
            if MusicComposition.objects.filter(title=title).exists():
                continue
                
            # Generate simulated MIDI data
            midi_sequence = []
            duration = random.randint(60, 240)
            
            for j in range(duration // 4):
                note = random.choice(['C', 'D', 'E', 'F', 'G', 'A', 'B'])
                octave = random.randint(3, 6)
                velocity = random.randint(60, 100)
                
                midi_sequence.append({
                    'time': j * 4,
                    'note': f"{note}{octave}",
                    'velocity': velocity,
                    'duration': random.uniform(1, 3)
                })
            
            composition = MusicComposition.objects.create(
                title=title,
                user=random.choice(users),
                genre=random.choice(genres),
                tempo=random.choice(tempos),
                key_signature=random.choice(keys),
                duration=duration,
                ai_model_version='v1.0',
                generation_parameters={
                    'genre': random.choice(genres).name,
                    'mood': random.choice(['happy', 'sad', 'energetic', 'calm']),
                    'complexity': random.choice(['simple', 'moderate', 'complex'])
                },
                midi_data=json.dumps(midi_sequence),
                is_public=random.choice([True, False]),
                play_count=random.randint(0, 1000),
                like_count=random.randint(0, 100)
            )
            
            self.stdout.write(f'Created composition: {composition.title}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated composition data!')
        )