from __future__ import annotations

from typing import Optional

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from .models import Usuario


@database_sync_to_async
def _get_usuario_from_session(session) -> Optional[Usuario]:
    if session is None:
        return None
    user_id = session.get('usuario_id')
    if not user_id:
        return None
    try:
        return Usuario.objects.get(pk=user_id)
    except Usuario.DoesNotExist:
        return None


class UsuarioAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope['usuario'] = await _get_usuario_from_session(scope.get('session'))
        return await super().__call__(scope, receive, send)
