from __future__ import annotations

from typing import Any, Dict, Optional

from django.templatetags.static import static

from .models import Conversation, Message, Usuario


def get_avatar_url(user: Optional[Usuario]) -> str:
    if user and user.foto:
        try:
            return user.foto.url
        except ValueError:
            pass
    return static('img/default-avatar.svg')


def serialize_user(user: Optional[Usuario]) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    return {
        'id': user.id,
        'name': user.nome,
        'handle': f"@{user.username}" if user.username else '',
        'avatar_url': get_avatar_url(user),
    }


def serialize_message(message: Message, current_user: Usuario) -> Dict[str, Any]:
    is_self = message.autor_id == current_user.id
    is_deleted_for_all = message.deleted_for_everyone
    if is_deleted_for_all:
        deleted_by_name = message.deleted_by.nome if message.deleted_by else 'Usuário'
        display_text = f'{deleted_by_name} apagou esta mensagem.'
    else:
        display_text = message.texto

    return {
        'id': message.id,
        'conversation_id': message.conversation_id,
        'text': '' if is_deleted_for_all else display_text,
        'display_text': display_text,
        'created_at': message.created_at.isoformat(),
        'author': serialize_user(message.autor),
        'is_self': is_self,
        'is_deleted_for_all': is_deleted_for_all,
        'deleted_label': display_text if is_deleted_for_all else None,
        'can_delete_for_self': True,
        'can_delete_for_all': is_self and not is_deleted_for_all,
    }


def serialize_conversation(conversation: Conversation, current_user: Usuario) -> Dict[str, Any]:
    other = conversation.other_participant(current_user) or current_user
    last_message = (
        conversation.messages
        .exclude(deleted_for=current_user)
        .order_by('-created_at')
        .first()
    )
    if last_message and last_message.deleted_for_everyone:
        preview_text = serialize_message(last_message, current_user)['display_text']
    elif last_message:
        preview_text = last_message.texto
    else:
        preview_text = ''
    return {
        'id': conversation.id,
        'partner': serialize_user(other),
        'last_message': preview_text,
        'last_message_at': last_message.created_at.isoformat() if last_message else None,
    }
