from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters import rest_framework as filters
from .models import AIModel, MusicTheoryRule, GenerationRequest, TrainingDataset, ModelTrainingJob
from .serializers import (
    AIModelSerializer, MusicTheoryRuleSerializer, GenerationRequestSerializer,
    GenerationRequestStatusSerializer, TrainingDatasetSerializer, 
    ModelTrainingJobSerializer, CompositionAnalysisSerializer,
    GenerationParametersSerializer, AIModelRecommendationSerializer
)
from .ai_engine import AICompositionEngine, MusicTheoryAnalyzer
from composition.models import MusicComposition, Genre
import json
from django.utils import timezone


class AIModelFilter(filters.FilterSet):
    """Filter for AI models"""
    model_type = filters.ChoiceFilter(choices=AIModel.MODEL_TYPES)
    is_active = filters.BooleanFilter()
    is_premium = filters.BooleanFilter()
    min_quality = filters.NumberFilter(field_name='quality_score', lookup_expr='gte')
    
    class Meta:
        model = AIModel
        fields = ['model_type', 'is_active', 'is_premium', 'min_quality']


class AIModelListView(generics.ListAPIView):
    """List available AI models"""
    serializer_class = AIModelSerializer
    permission_classes = [AllowAny]
    filterset_class = AIModelFilter
    ordering = ['-quality_score', '-created_at']
    
    def get_queryset(self):
        return AIModel.objects.filter(is_active=True).prefetch_related('supported_genres')


class AIModelDetailView(generics.RetrieveAPIView):
    """Get detailed information about an AI model"""
    serializer_class = AIModelSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return AIModel.objects.filter(is_active=True).prefetch_related('supported_genres')


class MusicTheoryRuleListView(generics.ListAPIView):
    """List available music theory rules"""
    serializer_class = MusicTheoryRuleSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_fields = ['rule_type', 'is_active']
    ordering = ['rule_type', 'name']
    
    def get_queryset(self):
        return MusicTheoryRule.objects.filter(is_active=True).prefetch_related('genres')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommend_ai_model(request):
    """Recommend AI models based on user preferences and parameters"""
    serializer = GenerationParametersSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    user_profile = getattr(request.user, 'profile', None)
    
    # Get all active models
    models = AIModel.objects.filter(is_active=True).prefetch_related('supported_genres')
    recommendations = []
    
    for model in models:
        match_score = 0.5  # Base score
        reasons = []
        
        # Check genre compatibility
        if data.get('genre_id'):
            try:
                genre = Genre.objects.get(id=data['genre_id'])
                if genre in model.supported_genres.all():
                    match_score += 0.2
                    reasons.append(f"Optimized for {genre.name}")
            except Genre.DoesNotExist:
                pass
        
        # Check user experience level
        if user_profile:
            if user_profile.music_experience == 'beginner' and model.model_type == 'transformer':
                match_score += 0.1
                reasons.append("Good for beginners")
            elif user_profile.music_experience == 'professional' and model.model_type in ['vae', 'gan']:
                match_score += 0.15
                reasons.append("Advanced model for professionals")
        
        # Check creativity level compatibility
        creativity = data.get('creativity_level', 0.7)
        if creativity > 0.8 and model.model_type in ['gan', 'diffusion']:
            match_score += 0.1
            reasons.append("High creativity potential")
        elif creativity < 0.5 and model.model_type == 'transformer':
            match_score += 0.1
            reasons.append("Structured and predictable output")
        
        # Check quality score
        match_score += model.quality_score / 10 * 0.2
        
        # Estimate generation time
        base_time = data.get('duration', 60)
        estimated_time = int(base_time / model.generation_speed)
        
        if not reasons:
            reasons = ["General purpose model"]
        
        recommendations.append({
            'model': model,
            'match_score': min(match_score, 1.0),
            'reasons': reasons,
            'estimated_time': estimated_time
        })
    
    # Sort by match score
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Return top 5 recommendations
    serializer = AIModelRecommendationSerializer(recommendations[:5], many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_composition(request):
    """Start AI composition generation"""
    serializer = GenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Create generation request
    generation_request = serializer.save(user=request.user)
    
    # Start generation process (in a real app, this would be async)
    try:
        ai_model = generation_request.ai_model
        engine = AICompositionEngine(ai_model)
        
        # Generate composition
        result = engine.generate_composition(generation_request)
        
        if result['success']:
            # Create the composition in the database
            composition_data = result['composition_data']
            composition = MusicComposition.objects.create(
                title=composition_data['title'],
                user=request.user,
                genre=generation_request.genre,
                tempo=generation_request.tempo,
                key_signature=generation_request.key_signature,
                duration=generation_request.duration,
                ai_model_version=ai_model.version,
                generation_parameters=composition_data.get('generation_parameters', {}),
                midi_data=result.get('midi_data', ''),
                is_public=True
            )
            
            generation_request.generated_composition = composition
            generation_request.save()
            
            return Response({
                'request_id': generation_request.id,
                'composition_id': composition.id,
                'status': generation_request.status,
                'analysis': result.get('analysis', {})
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'request_id': generation_request.id,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        generation_request.status = 'failed'
        generation_request.error_message = str(e)
        generation_request.save()
        
        return Response({
            'request_id': generation_request.id,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerationRequestListView(generics.ListAPIView):
    """List user's generation requests"""
    serializer_class = GenerationRequestSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        return GenerationRequest.objects.filter(
            user=self.request.user
        ).select_related('ai_model', 'genre', 'generated_composition')


class GenerationRequestDetailView(generics.RetrieveAPIView):
    """Get detailed information about a generation request"""
    serializer_class = GenerationRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return GenerationRequest.objects.filter(
            user=self.request.user
        ).select_related('ai_model', 'genre', 'generated_composition')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generation_status(request, request_id):
    """Get the status of a generation request"""
    generation_request = get_object_or_404(
        GenerationRequest,
        id=request_id,
        user=request.user
    )
    
    serializer = GenerationRequestStatusSerializer(generation_request)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_composition(request, composition_id):
    """Analyze a composition using music theory rules"""
    try:
        composition = get_object_or_404(
            MusicComposition,
            id=composition_id,
            user=request.user
        )
        
        analyzer = MusicTheoryAnalyzer()
        
        # Convert composition to analysis format
        composition_data = {
            'key': composition.key_signature,
            'tempo': composition.tempo,
            'duration': composition.duration,
        }
        
        # Parse MIDI data if available
        if composition.midi_data:
            try:
                midi_data = json.loads(composition.midi_data)
                composition_data.update(midi_data)
            except json.JSONDecodeError:
                pass
        
        # Perform analysis
        analysis = analyzer.suggest_improvements(composition_data)
        
        serializer = CompositionAnalysisSerializer(analysis)
        return Response(serializer.data)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrainingDatasetListView(generics.ListAPIView):
    """List available training datasets"""
    serializer_class = TrainingDatasetSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        return TrainingDataset.objects.all().prefetch_related('genres')


class ModelTrainingJobListView(generics.ListAPIView):
    """List model training jobs"""
    serializer_class = ModelTrainingJobSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ModelTrainingJob.objects.all().select_related('ai_model', 'dataset')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_model_training(request):
    """Start training a new AI model (admin only for now)"""
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # This would implement model training logic
    return Response({
        'message': 'Model training feature coming soon'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['GET'])
@permission_classes([AllowAny])
def ai_capabilities(request):
    """Get overview of AI capabilities"""
    models = AIModel.objects.filter(is_active=True)
    rules = MusicTheoryRule.objects.filter(is_active=True)
    
    capabilities = {
        'total_models': models.count(),
        'model_types': list(models.values_list('model_type', flat=True).distinct()),
        'supported_genres': list(
            set([genre.name for model in models.prefetch_related('supported_genres') 
                 for genre in model.supported_genres.all()])
        ),
        'theory_rules': {
            'total': rules.count(),
            'types': list(rules.values_list('rule_type', flat=True).distinct())
        },
        'generation_limits': {
            'max_duration': max(models.values_list('max_duration', flat=True)) if models else 300,
            'sample_rates': list(models.values_list('sample_rate', flat=True).distinct()),
        }
    }
    
    return Response(capabilities)
