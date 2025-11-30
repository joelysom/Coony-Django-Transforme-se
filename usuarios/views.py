from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from .forms import RegistrationForm, LoginForm, PostForm, CommentForm
from .models import Usuario, Post, Comment


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
        
        # Try to find user by email or username
        user = None
        try:
            if '@' in email_or_username:
                user = Usuario.objects.get(email=email_or_username)
            else:
                user = Usuario.objects.get(nome=email_or_username)
        except Usuario.DoesNotExist:
            pass

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
