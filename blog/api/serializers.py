from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Post, Comment, Category, UserProfile, Notification

class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'created_date', 'post_count']

class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    post_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'profile', 'post_count']
    
    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'bio': profile.bio,
                'location': profile.location,
                'website': profile.website,
                'avatar': profile.avatar.url if profile.avatar else None,
                'email_verified': profile.email_verified
            }
        except UserProfile.DoesNotExist:
            return {}

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'location', 'website', 'avatar', 'birth_date', 'email_verified']

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'parent', 'text', 'created_date', 'updated_date', 'is_active', 'likes', 'like_count', 'replies']
        read_only_fields = ['author', 'created_date', 'updated_date', 'likes']
    
    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.filter(is_active=True), many=True).data
        return []

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'content', 'excerpt', 'author', 'category', 'status', 'created_date', 'published_date', 'updated_date', 'image', 'views', 'likes', 'tags', 'like_count', 'comment_count', 'comments']
        read_only_fields = ['author', 'created_date', 'published_date', 'updated_date', 'views', 'likes']
    
    def get_comments(self, obj):
        comments = obj.comments.filter(is_active=True, parent=None).order_by('-created_date')[:5]
        return CommentSerializer(comments, many=True).data

class PostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'excerpt', 'author', 'category', 'status', 'created_date', 'published_date', 'image', 'views', 'likes', 'tags', 'like_count', 'comment_count']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 'created_date', 'related_post', 'related_comment']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)