from django.urls import path
from . import views

app_name = 'ml_engine'

urlpatterns = [
    # AI Models
    path('api/models/', views.AIModelListView.as_view(), name='ai-model-list'),
    path('api/models/<int:pk>/', views.AIModelDetailView.as_view(), name='ai-model-detail'),
    path('api/models/recommend/', views.recommend_ai_model, name='recommend-ai-model'),
    
    # Music Theory Rules
    path('api/theory-rules/', views.MusicTheoryRuleListView.as_view(), name='theory-rules'),
    
    # Composition Generation
    path('api/generate/', views.generate_composition, name='generate-composition'),
    path('api/requests/', views.GenerationRequestListView.as_view(), name='generation-requests'),
    path('api/requests/<int:pk>/', views.GenerationRequestDetailView.as_view(), name='generation-request-detail'),
    path('api/requests/<int:request_id>/status/', views.generation_status, name='generation-status'),
    
    # Analysis
    path('api/analyze/<int:composition_id>/', views.analyze_composition, name='analyze-composition'),
    
    # Training (Admin)
    path('api/datasets/', views.TrainingDatasetListView.as_view(), name='training-datasets'),
    path('api/training-jobs/', views.ModelTrainingJobListView.as_view(), name='training-jobs'),
    path('api/train/', views.start_model_training, name='start-training'),
    
    # General
    path('api/capabilities/', views.ai_capabilities, name='ai-capabilities'),
]