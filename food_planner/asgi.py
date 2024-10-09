"""
ASGI config for food_planner project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import django_eventstream

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_planner.settings.dev')

application = ProtocolTypeRouter({
    'http': URLRouter([
        path('core/rooms/<latitude>/events/', AuthMiddlewareStack(
            URLRouter(django_eventstream.routing.urlpatterns)
        ), { 'format-channels': ['room-{latitude}'] }),

        path('events/', AuthMiddlewareStack(
            URLRouter(django_eventstream.routing.urlpatterns)
        ), { 'channels': ['food_planner_channel'] }),
        
        re_path(r'', get_asgi_application()),
    ]),
})
