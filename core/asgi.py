import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.dev')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from ordering.routing import websocket_urlpatterns

# WhiteNoise middleware (configured in settings) handles static files for both
# dev and production. ASGIStaticFilesHandler is not needed and conflicts with
# WhiteNoise when DEBUG=False.
application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
