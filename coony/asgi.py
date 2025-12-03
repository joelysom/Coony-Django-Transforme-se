"""ASGI config for Coony with HTTP + WebSocket routing."""

import os

import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coony.settings')
django.setup()

from usuarios.realtime import UsuarioAuthMiddleware  # noqa: E402
from usuarios.routing import websocket_urlpatterns  # noqa: E402

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
	'http': django_asgi_app,
	'websocket': SessionMiddlewareStack(
		UsuarioAuthMiddleware(
			URLRouter(websocket_urlpatterns)
		)
	),
})
