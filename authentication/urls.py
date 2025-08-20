from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/<str:username>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # User discovery
    path('users/', views.PublicUserListView.as_view(), name='user-list'),
    
    # Social features
    path('follow/<str:username>/', views.follow_user, name='follow-user'),
    path('<str:username>/followers/', views.UserFollowersView.as_view(), name='user-followers'),
    path('<str:username>/following/', views.UserFollowingView.as_view(), name='user-following'),
    
    # Activity feed
    path('feed/', views.UserActivityFeedView.as_view(), name='activity-feed'),
    
    # API key management
    path('api-keys/', views.APIKeyManagementView.as_view(), name='api-keys'),
]