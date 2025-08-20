"""
URL configuration for ai_music_platform project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView

def api_root(request):
    """API root endpoint with links to all services"""
    return JsonResponse({
        'message': 'Welcome to AI Music Platform API',
        'services': {
            'composition': '/composition/api/',
            'streaming': '/streaming/api/', 
            'audio_processing': '/audio-processing/api/'
        },
        'websockets': {
            'audio_processing': '/ws/audio/processing/'
        },
        'documentation': '/api/docs/',
        'admin': '/admin/'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('composition/', include('composition.urls')),
    path('streaming/', include('streaming.urls')),
    path('audio-processing/', include('audio_processing.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
