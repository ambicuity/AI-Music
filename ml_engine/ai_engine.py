"""
AI Music Generation Engine

This module provides interfaces for AI-powered music composition.
Note: This is a simulation framework for demonstration. In production,
this would integrate with actual ML models like TensorFlow, PyTorch, etc.
"""

import json
import random
import time
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from .models import AIModel, GenerationRequest, MusicTheoryRule


class MusicTheoryAnalyzer:
    """Analyzes and suggests music theory improvements"""
    
    CHORD_PROGRESSIONS = {
        'pop': ['I', 'V', 'vi', 'IV'],
        'jazz': ['IIm7', 'V7', 'IMaj7', 'VIm7'],
        'classical': ['I', 'IV', 'V', 'I'],
        'blues': ['I7', 'IV7', 'I7', 'V7'],
    }
    
    SCALE_PATTERNS = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'dorian': [0, 2, 3, 5, 7, 9, 10],
        'blues': [0, 3, 5, 6, 7, 10],
    }
    
    def __init__(self):
        self.rules = MusicTheoryRule.objects.filter(is_active=True)
    
    def analyze_harmony(self, composition_data: Dict) -> Dict:
        """Analyze harmonic content and suggest improvements"""
        suggestions = []
        
        # Analyze chord progressions
        if 'chords' in composition_data:
            chords = composition_data['chords']
            if self._has_weak_progression(chords):
                suggestions.append({
                    'type': 'harmony',
                    'issue': 'Weak chord progression',
                    'suggestion': 'Consider using stronger cadences like V-I',
                    'confidence': 0.8
                })
        
        # Check for voice leading issues
        if 'voices' in composition_data:
            voice_leading_issues = self._analyze_voice_leading(composition_data['voices'])
            suggestions.extend(voice_leading_issues)
        
        return {
            'suggestions': suggestions,
            'harmony_score': self._calculate_harmony_score(composition_data),
            'theoretical_accuracy': self._check_theoretical_accuracy(composition_data)
        }
    
    def analyze_melody(self, composition_data: Dict) -> Dict:
        """Analyze melodic content and suggest improvements"""
        suggestions = []
        
        if 'melody' in composition_data:
            melody = composition_data['melody']
            
            # Check for melodic contour
            if self._has_poor_contour(melody):
                suggestions.append({
                    'type': 'melody',
                    'issue': 'Poor melodic contour',
                    'suggestion': 'Add more variety in melodic direction and interval sizes',
                    'confidence': 0.7
                })
            
            # Check for scale adherence
            scale_analysis = self._analyze_scale_usage(melody, composition_data.get('key', 'C'))
            if scale_analysis['out_of_scale_notes'] > 0.2:  # More than 20% out of scale
                suggestions.append({
                    'type': 'melody',
                    'issue': 'Excessive chromatic notes',
                    'suggestion': 'Consider reducing chromatic passages or adding harmonic support',
                    'confidence': 0.6
                })
        
        return {
            'suggestions': suggestions,
            'melody_score': self._calculate_melody_score(composition_data),
            'scale_adherence': self._check_scale_adherence(composition_data)
        }
    
    def suggest_improvements(self, composition_data: Dict) -> Dict:
        """Provide comprehensive suggestions for improvement"""
        harmony_analysis = self.analyze_harmony(composition_data)
        melody_analysis = self.analyze_melody(composition_data)
        
        # Combine all suggestions
        all_suggestions = (
            harmony_analysis['suggestions'] + 
            melody_analysis['suggestions']
        )
        
        # Sort by confidence
        all_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'overall_score': (
                harmony_analysis['harmony_score'] + 
                melody_analysis['melody_score']
            ) / 2,
            'suggestions': all_suggestions[:10],  # Top 10 suggestions
            'analysis': {
                'harmony': harmony_analysis,
                'melody': melody_analysis
            }
        }
    
    def _has_weak_progression(self, chords: List[str]) -> bool:
        """Check if chord progression is weak (simplified heuristic)"""
        # Simplified: check if there are any strong cadences
        strong_cadences = ['V-I', 'V7-I', 'ii-V-I']
        chord_pairs = [f"{chords[i]}-{chords[i+1]}" for i in range(len(chords)-1)]
        return not any(cadence in ''.join(chord_pairs) for cadence in strong_cadences)
    
    def _analyze_voice_leading(self, voices: List[List[int]]) -> List[Dict]:
        """Analyze voice leading between parts"""
        suggestions = []
        # Simplified analysis - check for parallel fifths/octaves
        for i in range(len(voices)-1):
            voice1, voice2 = voices[i], voices[i+1]
            if len(voice1) == len(voice2):
                for j in range(len(voice1)-1):
                    interval1 = abs(voice1[j] - voice2[j])
                    interval2 = abs(voice1[j+1] - voice2[j+1])
                    if interval1 == interval2 and interval1 in [7, 12]:  # Perfect 5th or octave
                        suggestions.append({
                            'type': 'voice_leading',
                            'issue': f'Parallel {"fifths" if interval1 == 7 else "octaves"}',
                            'suggestion': 'Avoid parallel perfect intervals',
                            'confidence': 0.9,
                            'location': f'Measure {j+1}'
                        })
        return suggestions
    
    def _has_poor_contour(self, melody: List[int]) -> bool:
        """Check if melody has poor contour (simplified)"""
        if len(melody) < 4:
            return False
        
        # Check for too much repetition
        unique_notes = len(set(melody))
        repetition_ratio = unique_notes / len(melody)
        
        # Check for too many large leaps
        large_leaps = sum(1 for i in range(len(melody)-1) if abs(melody[i+1] - melody[i]) > 7)
        leap_ratio = large_leaps / (len(melody) - 1)
        
        return repetition_ratio < 0.3 or leap_ratio > 0.3
    
    def _analyze_scale_usage(self, melody: List[int], key: str) -> Dict:
        """Analyze how well melody adheres to scale"""
        # Simplified: assume C major scale for now
        major_scale = [0, 2, 4, 5, 7, 9, 11]  # C major in semitones
        
        out_of_scale = 0
        for note in melody:
            if note % 12 not in major_scale:
                out_of_scale += 1
        
        return {
            'out_of_scale_notes': out_of_scale / len(melody),
            'scale_type': 'major',  # Simplified
            'key': key
        }
    
    def _calculate_harmony_score(self, composition_data: Dict) -> float:
        """Calculate harmony quality score (0-1)"""
        # Simplified scoring based on various factors
        score = 0.7  # Base score
        
        if 'chords' in composition_data:
            # Add score for variety in chords
            unique_chords = len(set(composition_data['chords']))
            total_chords = len(composition_data['chords'])
            variety_score = min(unique_chords / total_chords * 2, 1.0)
            score += variety_score * 0.3
        
        return min(score, 1.0)
    
    def _calculate_melody_score(self, composition_data: Dict) -> float:
        """Calculate melody quality score (0-1)"""
        # Simplified scoring
        score = 0.6  # Base score
        
        if 'melody' in composition_data:
            melody = composition_data['melody']
            
            # Check contour variety
            if not self._has_poor_contour(melody):
                score += 0.2
            
            # Check scale adherence
            scale_analysis = self._analyze_scale_usage(melody, composition_data.get('key', 'C'))
            if scale_analysis['out_of_scale_notes'] < 0.1:
                score += 0.2
        
        return min(score, 1.0)
    
    def _check_theoretical_accuracy(self, composition_data: Dict) -> float:
        """Check overall theoretical accuracy"""
        # Simplified calculation
        return random.uniform(0.7, 0.95)  # Simulation
    
    def _check_scale_adherence(self, composition_data: Dict) -> float:
        """Check scale adherence percentage"""
        if 'melody' not in composition_data:
            return 1.0
        
        scale_analysis = self._analyze_scale_usage(
            composition_data['melody'], 
            composition_data.get('key', 'C')
        )
        return 1.0 - scale_analysis['out_of_scale_notes']


class AICompositionEngine:
    """Main AI composition engine"""
    
    def __init__(self, model: AIModel):
        self.model = model
        self.theory_analyzer = MusicTheoryAnalyzer()
    
    def generate_composition(self, request: GenerationRequest) -> Dict:
        """Generate a music composition based on the request"""
        try:
            # Update request status
            request.status = 'processing'
            request.started_at = timezone.now()
            request.progress = 10
            request.save()
            
            # Simulate processing time
            self._simulate_processing(request)
            
            # Generate composition data
            composition_data = self._generate_music_data(request)
            
            # Apply music theory analysis and improvements
            if request.music_theory_rules.exists():
                composition_data = self._apply_theory_rules(composition_data, request)
                request.progress = 70
                request.save()
            
            # Final processing
            request.progress = 90
            request.save()
            
            # Create the final composition
            final_composition = self._create_composition_output(composition_data, request)
            
            # Complete the request
            request.status = 'completed'
            request.progress = 100
            request.completed_at = timezone.now()
            request.save()
            
            return {
                'success': True,
                'composition_data': composition_data,
                'analysis': self.theory_analyzer.suggest_improvements(composition_data)
            }
            
        except Exception as e:
            request.status = 'failed'
            request.error_message = str(e)
            request.save()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _simulate_processing(self, request: GenerationRequest):
        """Simulate AI processing with progress updates"""
        stages = [20, 35, 50]
        for progress in stages:
            time.sleep(0.5)  # Simulate processing time
            request.progress = progress
            request.save()
    
    def _generate_music_data(self, request: GenerationRequest) -> Dict:
        """Generate the actual music data (simulated)"""
        # This would interface with actual ML models in production
        
        # Generate basic structure
        duration = request.duration
        tempo = request.tempo
        key = request.key_signature
        
        # Generate chord progression
        genre_name = request.genre.name.lower() if request.genre else 'pop'
        base_progression = self.theory_analyzer.CHORD_PROGRESSIONS.get(genre_name, ['I', 'V', 'vi', 'IV'])
        
        # Repeat progression to fill duration
        measures = duration // (60 / tempo * 4)  # Approximate measures in 4/4
        chord_progression = (base_progression * ((measures // len(base_progression)) + 1))[:measures]
        
        # Generate melody
        scale = self.theory_analyzer.SCALE_PATTERNS['major']  # Simplified
        melody = self._generate_melody(measures * 4, scale, request.creativity_level)
        
        # Generate rhythm pattern
        rhythm = self._generate_rhythm_pattern(measures * 4, genre_name)
        
        # Generate bass line
        bass_line = self._generate_bass_line(chord_progression, scale)
        
        return {
            'title': request.title or f"AI Composition in {key}",
            'key': key,
            'tempo': tempo,
            'duration': duration,
            'chords': chord_progression,
            'melody': melody,
            'rhythm': rhythm,
            'bass_line': bass_line,
            'instruments': request.instruments or ['piano', 'strings'],
            'genre': genre_name,
            'mood': request.mood or 'neutral',
            'creativity_level': request.creativity_level,
            'generation_parameters': {
                'model': self.model.name,
                'version': self.model.version,
                'timestamp': timezone.now().isoformat()
            }
        }
    
    def _generate_melody(self, length: int, scale: List[int], creativity: float) -> List[int]:
        """Generate a melody using the scale"""
        melody = []
        current_note = 60  # Middle C
        
        for _ in range(length):
            # Apply creativity - higher creativity means more adventurous intervals
            if random.random() < creativity:
                # More creative interval choices
                interval = random.choice([-7, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 7, 12])
            else:
                # Conservative interval choices
                interval = random.choice([-2, -1, 0, 1, 2])
            
            current_note += interval
            
            # Constrain to reasonable range
            current_note = max(48, min(84, current_note))
            
            # Adjust to scale if not very creative
            if creativity < 0.8:
                octave = current_note // 12
                note_in_octave = current_note % 12
                if note_in_octave not in scale:
                    # Find nearest scale note
                    distances = [abs(note_in_octave - scale_note) for scale_note in scale]
                    closest_scale_note = scale[distances.index(min(distances))]
                    current_note = octave * 12 + closest_scale_note
            
            melody.append(current_note)
        
        return melody
    
    def _generate_rhythm_pattern(self, length: int, genre: str) -> List[Dict]:
        """Generate rhythm pattern"""
        patterns = {
            'pop': [1, 0, 0.5, 0, 1, 0, 0.5, 0],
            'jazz': [1, 0, 0.3, 0.7, 0.5, 0, 0.8, 0],
            'classical': [1, 0.3, 0.3, 0.3, 1, 0.3, 0.3, 0.3],
            'blues': [1, 0, 0.7, 0.3, 1, 0, 0.7, 0]
        }
        
        base_pattern = patterns.get(genre, patterns['pop'])
        rhythm = []
        
        for i in range(length):
            beat_strength = base_pattern[i % len(base_pattern)]
            rhythm.append({
                'position': i,
                'strength': beat_strength,
                'duration': 0.25  # Quarter note
            })
        
        return rhythm
    
    def _generate_bass_line(self, chord_progression: List[str], scale: List[int]) -> List[int]:
        """Generate bass line following chord progression"""
        bass_line = []
        
        # Simplified bass generation - use chord roots
        chord_roots = {
            'I': 0, 'ii': 2, 'iii': 4, 'IV': 5, 'V': 7, 'vi': 9, 'vii': 11,
            'I7': 0, 'ii7': 2, 'iii7': 4, 'IV7': 5, 'V7': 7, 'vi7': 9, 'vii7': 11
        }
        
        for chord in chord_progression:
            chord_clean = chord.replace('m', '').replace('7', '').replace('Maj', '')
            root = chord_roots.get(chord_clean, 0)
            bass_note = 36 + root  # Low C + interval
            
            # Add some bass line movement
            for _ in range(4):  # 4 beats per chord
                bass_line.append(bass_note + random.choice([0, -12, 12]))
        
        return bass_line
    
    def _apply_theory_rules(self, composition_data: Dict, request: GenerationRequest) -> Dict:
        """Apply music theory rules to improve composition"""
        rules = request.music_theory_rules.all()
        
        for rule in rules:
            if rule.rule_type == 'harmony':
                composition_data = self._apply_harmony_rule(composition_data, rule)
            elif rule.rule_type == 'melody':
                composition_data = self._apply_melody_rule(composition_data, rule)
            elif rule.rule_type == 'rhythm':
                composition_data = self._apply_rhythm_rule(composition_data, rule)
        
        return composition_data
    
    def _apply_harmony_rule(self, composition_data: Dict, rule: MusicTheoryRule) -> Dict:
        """Apply harmony-specific rules"""
        # Simplified rule application
        if 'avoid_parallel_fifths' in rule.parameters:
            # Modify chord voicings to avoid parallels
            pass
        
        return composition_data
    
    def _apply_melody_rule(self, composition_data: Dict, rule: MusicTheoryRule) -> Dict:
        """Apply melody-specific rules"""
        # Simplified rule application
        if 'limit_large_leaps' in rule.parameters:
            # Smooth out large melodic intervals
            melody = composition_data.get('melody', [])
            for i in range(len(melody) - 1):
                if abs(melody[i+1] - melody[i]) > 7:  # Larger than perfect 5th
                    # Insert intermediate note
                    intermediate = (melody[i] + melody[i+1]) // 2
                    melody[i+1] = intermediate
            composition_data['melody'] = melody
        
        return composition_data
    
    def _apply_rhythm_rule(self, composition_data: Dict, rule: MusicTheoryRule) -> Dict:
        """Apply rhythm-specific rules"""
        # Simplified rule application
        return composition_data
    
    def _create_composition_output(self, composition_data: Dict, request: GenerationRequest) -> Dict:
        """Create the final composition output format"""
        # This would generate actual audio files, MIDI, etc. in production
        return {
            'midi_data': self._generate_midi_simulation(composition_data),
            'audio_url': f'/media/compositions/ai_generated_{request.id}.wav',  # Simulated
            'score_data': composition_data,
            'metadata': {
                'generated_by': self.model.name,
                'generation_time': timezone.now().isoformat(),
                'parameters': composition_data.get('generation_parameters', {})
            }
        }
    
    def _generate_midi_simulation(self, composition_data: Dict) -> str:
        """Generate simulated MIDI data"""
        # In production, this would generate actual MIDI
        return json.dumps({
            'tracks': [
                {
                    'name': 'Melody',
                    'notes': composition_data.get('melody', [])
                },
                {
                    'name': 'Bass',
                    'notes': composition_data.get('bass_line', [])
                }
            ],
            'tempo': composition_data.get('tempo', 120),
            'time_signature': '4/4'
        }, indent=2)