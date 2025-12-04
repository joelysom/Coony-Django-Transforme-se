from collections import Counter
from django.core.exceptions import MultipleObjectsReturned
import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
from django.utils.timesince import timesince

from .forms import RegistrationForm, LoginForm, PostForm, CommentForm, EventoForm
from .models import Usuario, Post, Comment, Conversation, Message, PostLikeEvent, Evento
from .utils import normalize_username
from .chat_serializers import serialize_user, serialize_message, serialize_conversation


def _get_logged_user(request):
    uid = request.session.get('usuario_id')
    if not uid:
        return None
    try:
        return Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return None


def _json_auth_required(request):
    user = _get_logged_user(request)
    if not user:
        return None, JsonResponse({'detail': 'Autenticação requerida'}, status=401)
    return user, None


def _broadcast_message_event(message):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    async_to_sync(channel_layer.group_send)(
        f'chat_{message.conversation_id}',
        {
            'type': 'chat.message_event',
            'message_id': message.id,
            'conversation_id': message.conversation_id,
        }
    )


def index(request):
    """Render desktop version of the page (contains login/register forms)."""
    reg_form = RegistrationForm()
    login_form = LoginForm()
    return render(request, 'usuarios/index.html', {'reg_form': reg_form, 'login_form': login_form})


def mobile(request):
    """Render mobile version of the page (contains login/register forms)."""
    reg_form = RegistrationForm()
    login_form = LoginForm()
    return render(request, 'usuarios/mobile.html', {'reg_form': reg_form, 'login_form': login_form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # set hashed password
            user.set_password(form.cleaned_data['password'])
            user.save()
            # log the user in by storing id in session
            request.session['usuario_id'] = user.id
            messages.success(request, f'Bem-vindo, {user.nome}! Cadastro realizado com sucesso.', extra_tags='toast')
            return redirect('dashboard')
        else:
            # re-render index with errors
            login_form = LoginForm()
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error, extra_tags='toast')
            return render(request, 'usuarios/index.html', {'reg_form': form, 'login_form': login_form})
    return redirect('index')


def login_view(request):
    if request.method == 'POST':
        email_or_username = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email_or_username or not password:
            messages.error(request, 'Por favor, preencha todos os campos.', extra_tags='toast')
            form = LoginForm(request.POST)
            reg_form = RegistrationForm()
            template = 'usuarios/mobile.html' if request.user_agent.is_mobile else 'usuarios/index.html'
            return render(request, template, {
                'reg_form': reg_form,
                'login_form': form
            })
        
        identifier = email_or_username
        normalized_username = normalize_username(identifier)
        lookups = []
        if identifier.startswith('@'):
            lookups.append(('username', normalized_username))
        elif '@' in identifier:
            lookups.append(('email', identifier))
        else:
            lookups.append(('nome', identifier))
            if normalized_username:
                lookups.append(('username', normalized_username))

        user = None
        for field, value in lookups:
            if not value:
                continue
            try:
                user = Usuario.objects.get(**{field: value})
                break
            except (Usuario.DoesNotExist, MultipleObjectsReturned):
                continue

        if user and user.check_password(password):
            request.session['usuario_id'] = user.id
            messages.success(request, f'Bem-vindo de volta, {user.nome}!', extra_tags='toast')
            return redirect('dashboard')
        else:
            messages.error(request, 'Email/usuário ou senha inválidos.', extra_tags='toast')
            form = LoginForm(request.POST)
            reg_form = RegistrationForm()
            template = 'usuarios/mobile.html' if request.user_agent.is_mobile else 'usuarios/index.html'
            return render(request, template, {
                'reg_form': reg_form,
                'login_form': form
            })
    return redirect('index')


def logout_view(request):
    usuario_nome = None
    uid = request.session.get('usuario_id')
    if uid:
        try:
            user = Usuario.objects.get(pk=uid)
            usuario_nome = user.nome
        except Usuario.DoesNotExist:
            pass
    
    request.session.pop('usuario_id', None)
    if usuario_nome:
        messages.success(request, f'Até logo, {usuario_nome}! Você foi desconectado.', extra_tags='toast')
    return redirect('index')


def dashboard(request):
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('index')
    try:
        user = Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return redirect('index')
    if getattr(request.user_agent, 'is_mobile', False):
        return redirect('dashboard_mobile')
    # Show events created by all users, most recent first
    eventos = Evento.objects.all().order_by('-data', '-hora', '-criado_em')
    return render(request, 'usuarios/dashboard.html', {'user': user, 'eventos': eventos})

def dashboard_mobile(request):
    """Render mobile version of the dashboard."""
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('index')
    try:
        user = Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return redirect('index')
    if not getattr(request.user_agent, 'is_mobile', False):
        return redirect('dashboard')
    # Show events created by all users, most recent first
    eventos = Evento.objects.all().order_by('-data', '-hora', '-criado_em')
    return render(request, 'usuarios/dashboard_mobile.html', {'user': user, 'eventos': eventos})

def social(request):
    """Render social network page."""
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('index')
    try:
        user = Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return redirect('index')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.autor = user
            post.save()
            messages.success(request, 'Post criado com sucesso!', extra_tags='toast')
            return redirect('social')
    else:
        form = PostForm()
    
    posts = Post.objects.all().order_by('-data_criacao')
    return render(request, 'usuarios/social.html', {
        'user': user,
        'form': form,
        'posts': posts,
        'comment_form': CommentForm()
    })


def eventos_list(request):
    """Render events listing page."""
    user = _get_logged_user(request)
    if not user:
        return redirect('index')
    
    eventos = Evento.objects.all().order_by('-data', '-hora', '-criado_em')
    return render(request, 'usuarios/eventos.html', {
        'user': user,
        'eventos': eventos,
    })


def evento_detail(request, evento_id):
    """Render event detail page."""
    user = _get_logged_user(request)
    if not user:
        return redirect('index')
    
    try:
        evento = Evento.objects.select_related('criador').get(pk=evento_id)
    except Evento.DoesNotExist:
        messages.error(request, 'Evento não encontrado.', extra_tags='toast')
        return redirect('eventos_list')
    
    return render(request, 'usuarios/evento_detail.html', {
        'user': user,
        'evento': evento,
    })


def create_event(request):
    user = _get_logged_user(request)
    if not user:
        return redirect('index')

    if request.method == 'POST':
        form = EventoForm(request.POST, request.FILES)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.criador = user
            evento.save()
            messages.success(
                request,
                f'Evento "{evento.titulo}" criado com sucesso!',
                extra_tags='toast'
            )
            return redirect('create_event')
        messages.error(request, 'Verifique os campos destacados e tente novamente.', extra_tags='toast')
    else:
        form = EventoForm()

    return render(request, 'usuarios/create_event.html', {
        'user': user,
        'form': form,
    })


def my_events(request):
    user = _get_logged_user(request)
    if not user:
        return redirect('index')

    search = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'future')

    now = timezone.localtime()
    future_filter = Q(data__gt=now.date()) | (Q(data=now.date()) & Q(hora__gte=now.time()))
    past_filter = Q(data__lt=now.date()) | (Q(data=now.date()) & Q(hora__lt=now.time()))

    eventos_qs = user.eventos.all()
    stats = {
        'total': eventos_qs.count(),
        'upcoming': eventos_qs.filter(future_filter).count(),
        'past': eventos_qs.filter(past_filter).count(),
    }

    if status == 'future':
        eventos_qs = eventos_qs.filter(future_filter)
    elif status == 'past':
        eventos_qs = eventos_qs.filter(past_filter)
    else:
        status = 'all'

    if search:
        eventos_qs = eventos_qs.filter(
            Q(titulo__icontains=search) |
            Q(local__icontains=search)
        )

    eventos = eventos_qs.order_by('data', 'hora')
    next_event = user.eventos.filter(future_filter).order_by('data', 'hora').first()

    return render(request, 'usuarios/my_events.html', {
        'user': user,
        'eventos': eventos,
        'search': search,
        'status': status,
        'stats': stats,
        'next_event': next_event,
    })


def notifications(request):
    user = _get_logged_user(request)
    if not user:
        return redirect('index')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'clear':
            request.session['notifications_cleared_at'] = timezone.now().timestamp()
            messages.info(request, 'Seu feed foi limpo. Novas interações aparecerão automaticamente.', extra_tags='toast')
            return redirect('notifications')

    notifications = []
    now = timezone.now()
    type_filter = (request.GET.get('type') or 'all').lower()
    search_query = request.GET.get('q', '').strip()

    cleared_at_ts = request.session.get('notifications_cleared_at')
    cleared_at = None
    if cleared_at_ts:
        try:
            cleared_at = timezone.datetime.fromtimestamp(float(cleared_at_ts), tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            cleared_at = None

    conversation_ids = list(user.chat_conversations.values_list('id', flat=True))
    if conversation_ids:
        message_events = (
            Message.objects
            .filter(conversation_id__in=conversation_ids)
            .exclude(autor=user)
            .exclude(deleted_for=user)
            .exclude(deleted_for_everyone=True)
            .select_related('autor', 'conversation')
            .order_by('-created_at')[:20]
        )
        chat_url = reverse('chat')
        for message in message_events:
            preview = message.texto.strip() if message.texto else ''
            notifications.append({
                'type': 'message',
                'icon': 'forum',
                'title': f'{message.autor.nome} respondeu no chat',
                'description': preview[:160] if preview else 'Você tem uma nova resposta na conversa.',
                'timestamp': message.created_at,
                'cta_url': chat_url,
                'cta_label': 'Abrir chat'
            })

    comment_events = (
        Comment.objects
        .filter(post__autor=user)
        .exclude(autor=user)
        .select_related('autor', 'post')
        .order_by('-data_criacao')[:20]
    )
    social_url = reverse('social')
    for comment in comment_events:
        post_excerpt = (comment.post.texto or '').strip()
        notifications.append({
            'type': 'comment',
            'icon': 'chat_bubble',
            'title': f'{comment.autor.nome} comentou no seu post',
            'description': comment.texto.strip()[:200] if comment.texto else 'Novo comentário no seu post.',
            'timestamp': comment.data_criacao,
            'post_excerpt': post_excerpt[:120] if post_excerpt else None,
            'cta_url': social_url,
            'cta_label': 'Ver na timeline'
        })

    like_events = (
        PostLikeEvent.objects
        .filter(post__autor=user)
        .exclude(usuario=user)
        .select_related('usuario', 'post')
        .order_by('-created_at')[:20]
    )
    for event in like_events:
        post_excerpt = (event.post.texto or '').strip()
        notifications.append({
            'type': 'like',
            'icon': 'favorite',
            'title': f'{event.usuario.nome} curtiu seu post',
            'description': post_excerpt[:200] if post_excerpt else 'Seu post recebeu um novo like.',
            'timestamp': event.created_at,
            'post_excerpt': post_excerpt[:120] if post_excerpt else None,
            'cta_url': social_url,
            'cta_label': 'Ver na timeline'
        })

    notifications.sort(key=lambda item: item['timestamp'] or now, reverse=True)
    notifications = notifications[:60]

    if cleared_at:
        notifications = [item for item in notifications if (item.get('timestamp') or now) > cleared_at]

    type_counts = Counter(item['type'] for item in notifications)
    stats = {
        'total': len(notifications),
        'message': type_counts.get('message', 0),
        'comment': type_counts.get('comment', 0),
        'like': type_counts.get('like', 0),
    }

    if type_filter not in {'message', 'comment', 'like', 'all'}:
        type_filter = 'all'

    filtered_notifications = notifications
    if type_filter != 'all':
        filtered_notifications = [item for item in filtered_notifications if item['type'] == type_filter]

    if search_query:
        lowered = search_query.lower()

        def matches(item):
            for field in ('title', 'description', 'post_excerpt'):
                value = item.get(field)
                if value and lowered in value.lower():
                    return True
            return False

        filtered_notifications = [item for item in filtered_notifications if matches(item)]

    filtered_notifications = filtered_notifications[:40]

    for item in filtered_notifications:
        ts = item.get('timestamp') or now
        delta = timesince(ts, now)
        item['relative_time'] = f'{delta} atrás' if delta else 'agora mesmo'

    return render(request, 'usuarios/notifications.html', {
        'user': user,
        'notifications': filtered_notifications,
        'stats': stats,
        'filter_type': type_filter,
        'search_query': search_query,
        'has_filters': bool(search_query) or type_filter != 'all',
        'last_synced': timezone.localtime(now),
        'cleared_at': timezone.localtime(cleared_at) if cleared_at else None,
    })


def chat(request):
    """Render chat interface."""
    user = _get_logged_user(request)
    if not user:
        return redirect('index')

    return render(request, 'usuarios/chat.html', {
        'user': user,
    })


@require_GET
def chat_conversations_api(request):
    user, error = _json_auth_required(request)
    if error:
        return error

    conversations = (Conversation.objects
                     .filter(participants=user)
                     .prefetch_related('participants', 'messages__autor', 'messages__deleted_by'))
    data = [serialize_conversation(conv, user) for conv in conversations]
    return JsonResponse({'conversations': data})


@require_GET
def chat_search_users_api(request):
    user, error = _json_auth_required(request)
    if error:
        return error

    term = request.GET.get('q', '').strip()
    if not term:
        return JsonResponse({'results': []})

    search_name = term.lstrip('@') if term.startswith('@') else term
    normalized_handle = normalize_username(term)

    filters = Q()
    if search_name:
        filters |= Q(nome__icontains=search_name)
    if normalized_handle:
        filters |= Q(username__icontains=normalized_handle)

    if not filters:
        return JsonResponse({'results': []})

    matches = (Usuario.objects
               .exclude(pk=user.pk)
               .filter(filters)
               .order_by('nome')[:8])

    results = [serialize_user(match) for match in matches]
    return JsonResponse({'results': results})


@require_POST
def chat_start_conversation_api(request):
    user, error = _json_auth_required(request)
    if error:
        return error

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)

    username = (payload.get('username') or '').strip().lstrip('@')
    normalized = normalize_username(username)
    if not normalized:
        return JsonResponse({'detail': 'Informe um @ válido.'}, status=400)

    try:
        partner = Usuario.objects.get(username=normalized)
    except Usuario.DoesNotExist:
        return JsonResponse({'detail': 'Usuário não encontrado.'}, status=404)

    if partner.id == user.id:
        return JsonResponse({'detail': 'Você não pode iniciar uma conversa consigo mesmo.'}, status=400)

    conversation = Conversation.get_or_create_private(user, partner)
    data = serialize_conversation(conversation, user)
    return JsonResponse({'conversation': data}, status=201)


@require_GET
def chat_messages_api(request, conversation_id):
    user, error = _json_auth_required(request)
    if error:
        return error

    try:
        conversation = Conversation.objects.prefetch_related('messages__autor', 'participants').get(pk=conversation_id, participants=user)
    except Conversation.DoesNotExist:
        return JsonResponse({'detail': 'Conversa não encontrada.'}, status=404)

    queryset = (conversation.messages
                .select_related('autor', 'deleted_by')
                .exclude(deleted_for=user))
    messages = [serialize_message(message, user) for message in queryset]
    return JsonResponse({'messages': messages})


@require_POST
def chat_send_message_api(request, conversation_id):
    user, error = _json_auth_required(request)
    if error:
        return error

    try:
        conversation = Conversation.objects.get(pk=conversation_id, participants=user)
    except Conversation.DoesNotExist:
        return JsonResponse({'detail': 'Conversa não encontrada.'}, status=404)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)

    text = (payload.get('text') or '').strip()
    if not text:
        return JsonResponse({'detail': 'A mensagem não pode estar vazia.'}, status=400)

    message = Message.objects.create(conversation=conversation, autor=user, texto=text)
    conversation.touch()
    _broadcast_message_event(message)

    return JsonResponse({'message': serialize_message(message, user)}, status=201)


@require_POST
def chat_delete_message_api(request, message_id):
    user, error = _json_auth_required(request)
    if error:
        return error

    try:
        message = (Message.objects
                   .select_related('conversation', 'autor', 'deleted_by')
                   .prefetch_related('conversation__participants')
                   .get(pk=message_id, conversation__participants=user))
    except Message.DoesNotExist:
        return JsonResponse({'detail': 'Mensagem não encontrada.'}, status=404)

    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)

    scope = (payload.get('scope') or 'self').lower()
    if scope not in {'self', 'all'}:
        return JsonResponse({'detail': 'Escopo inválido.'}, status=400)

    if scope == 'all':
        if message.autor_id != user.id:
            return JsonResponse({'detail': 'Você só pode apagar para todos as mensagens que enviou.'}, status=403)
        if message.deleted_for_everyone:
            return JsonResponse({'detail': 'Esta mensagem já foi apagada para todos.'}, status=400)

        message.deleted_for_everyone = True
        message.deleted_for_everyone_at = timezone.now()
        message.deleted_by = user
        message.save(update_fields=['deleted_for_everyone', 'deleted_for_everyone_at', 'deleted_by'])
        message.conversation.touch()
        _broadcast_message_event(message)
        return JsonResponse({
            'scope': 'all',
            'message': serialize_message(message, user),
            'conversation': serialize_conversation(message.conversation, user)
        })

    # Delete for self (default)
    message.deleted_for.add(user)
    conversation = message.conversation
    return JsonResponse({
        'scope': 'self',
        'message_id': message.id,
        'conversation': serialize_conversation(conversation, user)
    })


def like_post(request, post_id):
    uid = request.session.get('usuario_id')
    if not uid or request.method != 'POST':
        return redirect('social')
    try:
        user = Usuario.objects.get(pk=uid)
        post = Post.objects.get(pk=post_id)
    except (Usuario.DoesNotExist, Post.DoesNotExist):
        return redirect('social')

    if user in post.likes.all():
        post.likes.remove(user)
    else:
        post.likes.add(user)
        PostLikeEvent.objects.update_or_create(
            post=post,
            usuario=user,
            defaults={'created_at': timezone.now()}
        )
    return redirect('social')


def comment_post(request, post_id):
    uid = request.session.get('usuario_id')
    if not uid or request.method != 'POST':
        return redirect('social')
    try:
        user = Usuario.objects.get(pk=uid)
        post = Post.objects.get(pk=post_id)
    except (Usuario.DoesNotExist, Post.DoesNotExist):
        return redirect('social')

    form = CommentForm(request.POST)
    if form.is_valid():
        texto = form.cleaned_data['texto'].strip()
        if texto:
            Comment.objects.create(post=post, autor=user, texto=texto)
    return redirect('social')


@require_POST
def delete_post(request, post_id):
    """Allow the post author to delete their own post."""
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('index')

    try:
        user = Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return redirect('index')

    try:
        post = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        messages.error(request, 'Post não encontrado.', extra_tags='toast')
        return redirect('social')

    if post.autor_id != user.id:
        messages.error(request, 'Você só pode deletar suas próprias postagens.', extra_tags='toast')
        return redirect('social')

    post.delete()
    messages.success(request, 'Post removido com sucesso.', extra_tags='toast')
    return redirect('social')


def perfil(request):
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('index')
    try:
        user = Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return redirect('index')

    if request.method == 'POST':
        has_error = False
        nome = request.POST.get('nome', '').strip()
        username_input = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        localizacao = request.POST.get('localizacao', '').strip()
        modalidades = request.POST.get('modalidades', '').strip()
        bio = request.POST.get('bio', '').strip()
        foto = request.FILES.get('foto')
        remove_foto = request.POST.get('remove_foto') == '1'

        if nome:
            user.nome = nome
        if username_input:
            normalized_username = normalize_username(username_input)
            if not normalized_username:
                messages.error(request, 'Use apenas letras, números e hífen para o @.', extra_tags='toast')
                has_error = True
            elif Usuario.objects.exclude(pk=user.pk).filter(username=normalized_username).exists():
                messages.error(request, 'Este @ já está em uso. Escolha outro.', extra_tags='toast')
                has_error = True
            else:
                user.username = normalized_username
        else:
            messages.error(request, 'O @ do usuário não pode ficar vazio.', extra_tags='toast')
            has_error = True
        if email:
            user.email = email
        user.localizacao = localizacao or ''
        user.modalidades = modalidades or ''
        user.bio = bio or ''
        if foto:
            user.foto = foto
        elif remove_foto and user.foto:
            user.foto.delete(save=False)
            user.foto = None

        if not has_error:
            try:
                user.save()
                messages.success(request, 'Perfil atualizado com sucesso!', extra_tags='toast')
            except IntegrityError:
                user.refresh_from_db()
                messages.error(request, 'Este e-mail já está em uso. Escolha outro.', extra_tags='toast')

    modalidades_list = [m.strip() for m in (user.modalidades or '').split(',') if m.strip()]
    return render(request, 'usuarios/perfil.html', {
        'user': user,
        'modalidades': modalidades_list,
    })


@require_POST
def toggle_favorite_event(request, evento_id):
    """Toggle favorite for an event via AJAX POST. Returns JSON with new state."""
    user = _get_logged_user(request)
    if not user:
        return JsonResponse({'detail': 'Autenticação requerida'}, status=401)

    try:
        evento = Evento.objects.get(pk=evento_id)
    except Evento.DoesNotExist:
        return JsonResponse({'detail': 'Evento não encontrado.'}, status=404)

    if user in evento.favorited_by.all():
        evento.favorited_by.remove(user)
        favorited = False
    else:
        evento.favorited_by.add(user)
        favorited = True

    return JsonResponse({'favorited': favorited})
