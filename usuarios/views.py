from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import RegistrationForm, LoginForm
from .models import Usuario


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
            return redirect('dashboard')
        else:
            # re-render index with errors
            login_form = LoginForm()
            return render(request, 'usuarios/index.html', {'reg_form': form, 'login_form': login_form})
    return redirect('index')


def login_view(request):
    if request.method == 'POST':
        try:
            # Get raw form data
            email_or_username = request.POST.get('email')
            password = request.POST.get('password')
            
            # Try to find user by email or username
            try:
                if '@' in email_or_username:
                    user = Usuario.objects.get(email=email_or_username)
                else:
                    user = Usuario.objects.get(nome=email_or_username)
            except Usuario.DoesNotExist:
                raise ValueError('Credenciais inválidas.')

            if user.check_password(password):
                request.session['usuario_id'] = user.id
                return redirect('dashboard')
            else:
                raise ValueError('Credenciais inválidas.')

        except ValueError as e:
            # Create form with error
            form = LoginForm(request.POST)
            form.add_error(None, str(e))
            reg_form = RegistrationForm()
            template = 'usuarios/mobile.html' if request.user_agent.is_mobile else 'usuarios/index.html'
            return render(request, template, {
                'reg_form': reg_form,
                'login_form': form
            })
    return redirect('index')


def logout_view(request):
    request.session.pop('usuario_id', None)
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

def sidebar(request):
    """Render the sidebar component."""
    uid = request.session.get('usuario_id')
    if not uid:
        return redirect('index')
    try:
        user = Usuario.objects.get(pk=uid)
    except Usuario.DoesNotExist:
        request.session.pop('usuario_id', None)
        return redirect('index')
        
    response = render(request, 'usuarios/components/sidebar.html', {'user': user})
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response
