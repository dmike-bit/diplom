from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend
from blog .models import Post, Comment, Category, UserProfile, Notification
from .serializers import (
    PostSerializer, PostListSerializer, CommentSerializer, 
    CategorySerializer, UserSerializer, NotificationSerializer,
    RegisterSerializer, LoginSerializer
)
from blog.views import get_site_settings, is_user_banned

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().annotate(post_count=Count('posts'))
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author', 'category').prefetch_related('comments', 'likes')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'category', 'author']
    search_fields = ['title', 'content', 'excerpt', 'tags']
    ordering_fields = ['created_date', 'published_date', 'views', 'likes']
    ordering = ['-published_date']

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.request.user.is_anonymous:
            queryset = queryset.filter(status='published')
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='published') | Q(author=self.request.user)
            )
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        if is_user_banned(request.user):
            return Response({'error': 'Заблокированные пользователи не могут лайкать'}, status=status.HTTP_403_FORBIDDEN)
        
        post = self.get_object()
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return Response({
            'liked': liked,
            'like_count': post.likes.count()
        })

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = post.comments.filter(is_active=True, parent=None).order_by('-created_date')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author', 'post', 'parent').prefetch_related('replies', 'likes')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

    def perform_create(self, serializer):
        if is_user_banned(self.request.user):
            return Response({'error': 'Заблокированные пользователи не могут комментировать'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        if is_user_banned(request.user):
            return Response({'error': 'Заблокированные пользователи не могут лайкать'}, status=status.HTTP_403_FORBIDDEN)
        
        comment = self.get_object()
        if comment.likes.filter(id=request.user.id).exists():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            liked = True
        
        return Response({
            'liked': liked,
            'like_count': comment.likes.count()
        })

class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().select_related('profile').annotate(post_count=Count('blog_posts'))
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['get', 'put', 'patch'])
    def profile(self, request, pk=None):
        user = self.get_object()
        
        if request.method == 'GET':
            if user == request.user or request.user.is_staff:
                try:
                    profile = user.profile
                    return Response({
                        'user': UserSerializer(user).data,
                        'profile': {
                            'bio': profile.bio,
                            'location': profile.location,
                            'website': profile.website,
                            'avatar': profile.avatar.url if profile.avatar else None,
                            'birth_date': profile.birth_date,
                            'email_verified': profile.email_verified
                        }
                    })
                except UserProfile.DoesNotExist:
                    return Response({'user': UserSerializer(user).data, 'profile': None})
            else:
                return Response(UserSerializer(user).data)
        
        elif request.method in ['PUT', 'PATCH']:
            if user != request.user and not request.user.is_staff:
                return Response({'error': 'Нет прав доступа'}, status=status.HTTP_403_FORBIDDEN)
            
            # Update profile logic here
            return Response({'message': 'Profile updated successfully'})

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Уведомление помечено как прочитанное'})

    @action(detail=False, methods=['get'])
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False)[:10]
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if is_user_banned(user):
                return Response({'error': 'Аккаунт заблокирован'}, status=status.HTTP_403_FORBIDDEN)
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Вы успешно вышли из системы'})
    except Exception:
        return Response({'error': 'Неверный токен'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    posts = Post.objects.filter(author=user).order_by('-created_date')[:10]
    notifications = Notification.objects.filter(user=user, is_read=False)[:5]
    
    return Response({
        'user': UserSerializer(user).data,
        'recent_posts': PostListSerializer(posts, many=True).data,
        'unread_notifications': NotificationSerializer(notifications, many=True).data,
    })

@api_view(['GET'])
def site_info(request):
    """Публичная информация о сайте"""
    settings = get_site_settings()
    return Response({
        'site_name': settings.site_name,
        'site_description': settings.site_description,
        'posts_per_page': settings.posts_per_page,
        'allow_registration': settings.allow_registration,
        'allow_comments': settings.allow_comments,
    })
