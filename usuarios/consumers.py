from __future__ import annotations

from typing import Any, Dict, Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .chat_serializers import serialize_conversation, serialize_message
from .models import Conversation, Message, Usuario


class ChatConsumer(AsyncJsonWebsocketConsumer):
    conversation_id: Optional[int] = None

    async def connect(self):
        usuario: Optional[Usuario] = self.scope.get('usuario')
        if not usuario:
            await self.close(code=4401)
            return

        conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        if not conversation_id:
            await self.close(code=4400)
            return

        has_access = await self._user_in_conversation(usuario.id, conversation_id)
        if not has_access:
            await self.close(code=4403)
            return

        self.conversation_id = conversation_id
        self.group_name = f'chat_{conversation_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if getattr(self, 'group_name', None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def chat_message_event(self, event: Dict[str, Any]):
        usuario: Optional[Usuario] = self.scope.get('usuario')
        if not usuario:
            return

        message = await self._serialize_message(event['message_id'], usuario)
        conversation = await self._serialize_conversation(event['conversation_id'], usuario)
        if not message or not conversation:
            return
        payload = {
            'event': 'message',
            'message': message,
            'conversation': conversation,
        }
        await self.send_json(payload)

    @database_sync_to_async
    def _user_in_conversation(self, user_id: int, conversation_id: int) -> bool:
        return Conversation.objects.filter(id=conversation_id, participants__id=user_id).exists()

    @database_sync_to_async
    def _serialize_message(self, message_id: int, current_user: Usuario) -> Dict[str, Any]:
        try:
            message = (Message.objects
                       .select_related('autor', 'deleted_by', 'conversation')
                       .get(pk=message_id))
        except Message.DoesNotExist:
            return {}
        return serialize_message(message, current_user)

    @database_sync_to_async
    def _serialize_conversation(self, conversation_id: int, current_user: Usuario) -> Dict[str, Any]:
        try:
            conversation = (Conversation.objects
                            .prefetch_related('participants', 'messages__autor', 'messages__deleted_by')
                            .get(pk=conversation_id))
        except Conversation.DoesNotExist:
            return {}
        return serialize_conversation(conversation, current_user)
