from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'jobs', views.AudioProcessingJobViewSet, basename='job')
router.register(r'visualizations', views.AudioVisualizationViewSet, basename='visualization')
router.register(r'features', views.AudioFeaturesViewSet, basename='features')
router.register(r'sessions', views.RealtimeSessionViewSet, basename='session')

urlpatterns = [
    path('api/', include(router.urls)),
]