from rest_framework import serializers
from .models import AIModel, MusicTheoryRule, GenerationRequest, TrainingDataset, ModelTrainingJob
from composition.serializers import GenreSerializer


class AIModelSerializer(serializers.ModelSerializer):
    """AI Model serializer"""
    supported_genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = AIModel
        fields = [
            'id', 'name', 'model_type', 'version', 'description',
            'supported_genres', 'max_duration', 'sample_rate',
            'parameters', 'is_active', 'is_premium', 'training_completion',
            'quality_score', 'generation_speed', 'created_at'
        ]


class MusicTheoryRuleSerializer(serializers.ModelSerializer):
    """Music theory rule serializer"""
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = MusicTheoryRule
        fields = [
            'id', 'name', 'rule_type', 'description', 'parameters',
            'weight', 'genres', 'key_signatures', 'time_signatures',
            'is_active', 'created_at'
        ]


class GenerationRequestSerializer(serializers.ModelSerializer):
    """Generation request serializer"""
    ai_model = AIModelSerializer(read_only=True)
    ai_model_id = serializers.IntegerField(write_only=True)
    genre = GenreSerializer(read_only=True)
    genre_id = serializers.IntegerField(required=False, allow_null=True)
    music_theory_rules = MusicTheoryRuleSerializer(many=True, read_only=True)
    music_theory_rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = GenerationRequest
        fields = [
            'id', 'ai_model', 'ai_model_id', 'title', 'genre', 'genre_id',
            'duration', 'tempo', 'key_signature', 'creativity_level',
            'mood', 'instruments', 'style_reference', 'custom_parameters',
            'music_theory_rules', 'music_theory_rule_ids',
            'status', 'progress', 'error_message', 'generated_composition',
            'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['status', 'progress', 'error_message', 'generated_composition']
    
    def create(self, validated_data):
        music_theory_rule_ids = validated_data.pop('music_theory_rule_ids', [])
        request = GenerationRequest.objects.create(**validated_data)
        
        if music_theory_rule_ids:
            request.music_theory_rules.set(music_theory_rule_ids)
        
        return request


class GenerationRequestStatusSerializer(serializers.ModelSerializer):
    """Simplified serializer for status updates"""
    class Meta:
        model = GenerationRequest
        fields = ['id', 'status', 'progress', 'error_message']


class TrainingDatasetSerializer(serializers.ModelSerializer):
    """Training dataset serializer"""
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = TrainingDataset
        fields = [
            'id', 'name', 'description', 'total_tracks', 'total_duration',
            'genres', 'audio_format', 'sample_rate', 'bit_depth',
            'preprocessing_config', 'is_processed', 'processing_progress',
            'created_at', 'updated_at'
        ]


class ModelTrainingJobSerializer(serializers.ModelSerializer):
    """Model training job serializer"""
    ai_model = AIModelSerializer(read_only=True)
    dataset = TrainingDatasetSerializer(read_only=True)
    
    class Meta:
        model = ModelTrainingJob
        fields = [
            'id', 'ai_model', 'dataset', 'training_config',
            'epochs', 'batch_size', 'learning_rate',
            'status', 'current_epoch', 'loss_history', 'metrics',
            'created_at', 'started_at', 'completed_at'
        ]


class CompositionAnalysisSerializer(serializers.Serializer):
    """Serializer for music theory analysis results"""
    overall_score = serializers.FloatField()
    suggestions = serializers.ListField(
        child=serializers.DictField()
    )
    analysis = serializers.DictField()


class GenerationParametersSerializer(serializers.Serializer):
    """Serializer for AI generation parameters"""
    ai_model_id = serializers.IntegerField()
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    genre_id = serializers.IntegerField(required=False, allow_null=True)
    duration = serializers.IntegerField(min_value=10, max_value=600, default=60)
    tempo = serializers.IntegerField(min_value=60, max_value=200, default=120)
    key_signature = serializers.CharField(max_length=10, default='C')
    creativity_level = serializers.FloatField(min_value=0.0, max_value=1.0, default=0.7)
    mood = serializers.CharField(max_length=50, required=False, allow_blank=True)
    instruments = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    style_reference = serializers.CharField(max_length=200, required=False, allow_blank=True)
    custom_parameters = serializers.DictField(required=False, allow_empty=True)
    music_theory_rule_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )


class AIModelRecommendationSerializer(serializers.Serializer):
    """Serializer for AI model recommendations"""
    model = AIModelSerializer()
    match_score = serializers.FloatField()
    reasons = serializers.ListField(child=serializers.CharField())
    estimated_time = serializers.IntegerField(help_text="Estimated generation time in seconds")