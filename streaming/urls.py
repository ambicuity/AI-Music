from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'artists', views.ArtistViewSet)
router.register(r'albums', views.AlbumViewSet)
router.register(r'tracks', views.TrackViewSet)
router.register(r'playlists', views.PlaylistViewSet, basename='playlist')
router.register(r'listening', views.UserListeningViewSet, basename='listening')

urlpatterns = [
    path('api/', include(router.urls)),
]