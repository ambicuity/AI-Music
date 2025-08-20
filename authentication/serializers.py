from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile, UserFollowing, UserActivity, APIKey


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create user profile
        UserProfile.objects.create(user=user)
        return user


class UserLoginSerializer(serializers.Serializer):
    """User login serializer"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('Account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must provide username and password')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'bio', 'avatar', 'location', 'website',
            'favorite_genres', 'music_experience', 'preferred_instruments',
            'is_public', 'allow_collaboration', 'receive_notifications',
            'ai_creativity_level', 'preferred_ai_models',
            'total_compositions', 'total_collaborations', 'reputation_score',
            'followers_count', 'following_count', 'last_active'
        ]
    
    def get_followers_count(self, obj):
        return obj.user.followers.count()
    
    def get_following_count(self, obj):
        return obj.user.following.count()
    
    def update(self, instance, validated_data):
        # Update user fields
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()
        
        # Update profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for public views"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'profile')


class UserFollowingSerializer(serializers.ModelSerializer):
    """User following serializer"""
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)
    
    class Meta:
        model = UserFollowing
        fields = ('id', 'follower', 'following', 'created_at')


class UserActivitySerializer(serializers.ModelSerializer):
    """User activity serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'content_type', 
            'object_id', 'metadata', 'is_public', 'created_at'
        ]


class APIKeySerializer(serializers.ModelSerializer):
    """API key serializer (with sensitive data hidden)"""
    api_key = serializers.CharField(write_only=True)
    refresh_token = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'service_name', 'api_key', 'refresh_token',
            'expires_at', 'is_active', 'created_at'
        ]
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Hide sensitive data in responses
        data.pop('api_key', None)
        data.pop('refresh_token', None)
        data['has_key'] = bool(instance.api_key)
        return data