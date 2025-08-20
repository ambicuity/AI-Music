"""
ASGI config for ai_music_platform project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_music_platform.settings')

django_asgi_app = get_asgi_application()

# Import WebSocket URL patterns (we'll create these later)
from audio_processing import routing as audio_routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/audio/', URLRouter(audio_routing.websocket_urlpatterns)),
        ])
    ),
})
