from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Genre, MusicComposition, CompositionLike


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'description', 'created_at']


class MusicCompositionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    genre = GenreSerializer(read_only=True)
    genre_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = MusicComposition
        fields = [
            'id', 'title', 'user', 'genre', 'genre_id', 'tempo', 'key_signature',
            'duration', 'ai_model_version', 'generation_parameters', 'midi_data',
            'audio_file', 'created_at', 'updated_at', 'is_public', 'play_count',
            'like_count'
        ]
        read_only_fields = ['user', 'ai_model_version', 'play_count', 'like_count']

    def create(self, validated_data):
        genre_id = validated_data.pop('genre_id', None)
        if genre_id:
            try:
                validated_data['genre'] = Genre.objects.get(id=genre_id)
            except Genre.DoesNotExist:
                pass
        return super().create(validated_data)


class CompositionLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    composition = MusicCompositionSerializer(read_only=True)

    class Meta:
        model = CompositionLike
        fields = ['id', 'user', 'composition', 'created_at']