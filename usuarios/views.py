from django.core.exceptions import MultipleObjectsReturned
import json

from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.templatetags.static import static
from django.utils import timezone

from .forms import RegistrationForm, LoginForm, PostForm, CommentForm
from .models import Usuario, Post, Comment, Conversation, Message
from .utils import normalize_username


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


def _avatar_url(user):
    if user and user.foto:
        try:
            return user.foto.url
        except ValueError:
            pass
    return static('img/default-avatar.svg')


def _user_payload(user):
    if not user:
        return None
    return {
        'id': user.id,
        'name': user.nome,
        'handle': f"@{user.username}" if user.username else '',
        'avatar_url': _avatar_url(user),
    }


def _message_payload(message, current_user):
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
        'author': _user_payload(message.autor),
        'is_self': is_self,
        'is_deleted_for_all': is_deleted_for_all,
        'deleted_label': display_text if is_deleted_for_all else None,
        'can_delete_for_self': True,
        'can_delete_for_all': is_self and not is_deleted_for_all,
    }


def _conversation_payload(conversation, current_user):
    other = conversation.other_participant(current_user) or current_user
    last_message = (conversation.messages
                    .exclude(deleted_for=current_user)
                    .order_by('-created_at')
                    .first())
    if last_message and last_message.deleted_for_everyone:
        preview_text = _message_payload(last_message, current_user)['display_text']
    elif last_message:
        preview_text = last_message.texto
    else:
        preview_text = ''
    return {
        'id': conversation.id,
        'partner': _user_payload(other),
        'last_message': preview_text,
        'last_message_at': last_message.created_at.isoformat() if last_message else None,
    }


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
    
    return render(request, 'usuarios/dashboard.html', {'user': user})

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
    
    return render(request, 'usuarios/dashboard_mobile.html', {'user': user})

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
    data = [_conversation_payload(conv, user) for conv in conversations]
    return JsonResponse({'conversations': data})


@require_GET
def chat_search_users_api(request):
    user, error = _json_auth_required(request)
    if error:
        return error

    term = request.GET.get('q', '').strip()
    if not term:
        return JsonResponse({'results': []})

    normalized = normalize_username(term.lstrip('@')) if term.startswith('@') else normalize_username(term)
    filters = Q(nome__icontains=term)
    if normalized:
        filters |= Q(username__icontains=normalized)

    matches = (Usuario.objects
               .exclude(pk=user.pk)
               .filter(filters)
               .order_by('nome')[:8])

    results = [_user_payload(match) for match in matches]
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
    data = _conversation_payload(conversation, user)
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
    messages = [_message_payload(message, user) for message in queryset]
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

    return JsonResponse({'message': _message_payload(message, user)}, status=201)


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
        return JsonResponse({
            'scope': 'all',
            'message': _message_payload(message, user),
            'conversation': _conversation_payload(message.conversation, user)
        })

    # Delete for self (default)
    message.deleted_for.add(user)
    conversation = message.conversation
    return JsonResponse({
        'scope': 'self',
        'message_id': message.id,
        'conversation': _conversation_payload(conversation, user)
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
