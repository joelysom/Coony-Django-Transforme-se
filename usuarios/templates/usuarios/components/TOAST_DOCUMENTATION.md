# Sistema de Notificações Toast - Documentação

## 📱 React Toaster Style Notification System

Sistema de notificações similar ao React Toaster, implementado em JavaScript puro + Django Framework.

---

## 🎨 Features

- ✅ **4 tipos de notificações**: Success, Error, Warning, Info
- ✅ **Material Design Icons**: Ícones do Google Fonts
- ✅ **Animações suaves**: Slide in/out com 300ms
- ✅ **Auto-dismiss**: Desaparece após 3 segundos
- ✅ **Botão de fechar**: Fechar manualmente
- ✅ **Progress bar**: Animação visual do tempo restante
- ✅ **Responsivo**: Funciona em mobile (topo direito ou topo inteiro em mobile)
- ✅ **Django Integration**: Usa django.contrib.messages
- ✅ **Sem dependências**: JavaScript puro

---

## 🚀 Como Usar

### No JavaScript (Client-Side)

```javascript
// Success
Toast.success('Conta criada com sucesso!', 'Bem-vindo!');

// Error
Toast.error('Email já cadastrado!', 'Erro ao registrar');

// Warning
Toast.warning('Este campo é obrigatório', 'Aviso!');

// Info
Toast.info('Verifique seu email', 'Confirmação');

// Custom com duração
Toast.success('Salvo!', null, 5000); // 5 segundos

// Remover específico
const id = Toast.success('Teste');
Toast.remove(id);

// Limpar todos
Toast.clear();
```

### No Django (Server-Side)

```python
from django.contrib import messages

# Success
messages.success(request, 'Bem-vindo de volta!', extra_tags='toast')

# Error
messages.error(request, 'Email ou senha inválidos', extra_tags='toast')

# Warning
messages.warning(request, 'Confirme seu email', extra_tags='toast')

# Info
messages.info(request, 'Atualizando perfil...', extra_tags='toast')
```

---

## 📁 Arquivos Criados

```
usuarios/templates/usuarios/components/
├── toast.html           # Sistema de notificação (HTML + CSS + JS)
└── messages.html        # Integração com Django messages
```

### Incluir em seu template:

```html
<!-- Toast Container + JS -->
{% include 'usuarios/components/toast.html' %}

<!-- Django Messages como Toasts -->
{% include 'usuarios/components/messages.html' %}
```

---

## 🎯 Tipos de Notificação

### 1. Success ✓
- Cor: Verde (#10b981)
- Uso: Confirmação de ação bem-sucedida
- Exemplo: Login, Cadastro, Salvar

### 2. Error ✕
- Cor: Vermelho (#ef4444)
- Uso: Erro na operação
- Exemplo: Validação, Falha de autenticação

### 3. Warning ⚠
- Cor: Amarelo (#f59e0b)
- Uso: Aviso importante
- Exemplo: Confirmação necessária

### 4. Info ℹ
- Cor: Azul (#3b82f6)
- Uso: Informação importante
- Exemplo: Status da operação

---

## 🎨 Customização

### Mudar cores (editar toast.html):

```css
.toast.success {
  border-left-color: #YOUR_COLOR;
  background: #YOUR_LIGHT_COLOR;
}
```

### Mudar duração padrão:

```javascript
Toast.success('Mensagem', 'Título', 5000); // 5 segundos
Toast.success('Mensagem', 'Título', 0);   // Não desaparece
```

### Mudar posição:

```css
#toast-container {
  top: 20px;
  right: 20px;
  /* Mude para: */
  /* top: 20px; left: 20px; */
  /* bottom: 20px; right: 20px; */
}
```

---

## 📱 Responsiveness

### Desktop (> 768px)
- Posição: Topo direito (top: 20px, right: 20px)
- Largura: 400px máx

### Mobile (≤ 768px)
- Posição: Topo (full width)
- Largura: 100% - 20px padding
- Melhor visibilidade em telas pequenas

---

## 🔄 Flow Completo - Exemplo Login

### 1. Usuário entra com email/senha
```html
<form action="{% url 'login' %}" method="post">
  <input name="email" placeholder="Email ou usuário">
  <input type="password" name="password">
  <button>Entrar</button>
</form>
```

### 2. Django valida e responde
```python
def login_view(request):
    if user and user.check_password(password):
        request.session['usuario_id'] = user.id
        messages.success(request, f'Bem-vindo, {user.nome}!')
        return redirect('dashboard')
    else:
        messages.error(request, 'Credenciais inválidas!')
        return render(request, 'usuarios/index.html', {...})
```

### 3. Template renderiza mensagens como toast
```html
{% include 'usuarios/components/toast.html' %}
{% include 'usuarios/components/messages.html' %}
```

### 4. JavaScript exibe notificação
- Toast aparece no canto superior direito
- Animação de slide-in
- Exibe por 3 segundos
- Animação de progress bar
- Desaparece automaticamente ou ao clicar em fechar

---

## 🛠 Integração com Views

### Já implementado em:
- ✅ `login_view()` - Sucesso/Erro ao logar
- ✅ `register_view()` - Sucesso/Erro ao registrar
- ✅ `logout_view()` - Mensagem de despedida
- ✅ Todas as páginas dashboard

### Para adicionar a novas views:

```python
from django.contrib import messages

def minha_view(request):
    if request.method == 'POST':
        try:
            # ... sua lógica ...
            messages.success(request, 'Operação realizada!')
            return redirect('sucesso')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
            return render(request, 'meu_template.html')
```

---

## 🎬 Animações

### Entrada (slideIn)
- Duração: 300ms
- Direção: Esquerda → Direita
- Easing: ease-out

### Saída (slideOut)
- Duração: 300ms
- Direção: Direita → Esquerda
- Easing: ease-out

### Progress Bar
- Duração: 3s (configurável)
- Animação: Largura 100% → 0%

---

## 🔌 API Completa

```javascript
// Mostrar genérico
Toast.show(message, type, title, duration)
  // type: 'success' | 'error' | 'warning' | 'info'
  // duration: milliseconds (0 = não desaparece)

// Shortcuts
Toast.success(message, title, duration)
Toast.error(message, title, duration)
Toast.warning(message, title, duration)
Toast.info(message, title, duration)

// Gerenciamento
Toast.remove(toastId)    // Remove específico
Toast.clear()            // Remove todos
```

---

## 📲 Exemplo Completo - Criar Evento

```python
# views.py
def criar_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save()
            messages.success(
                request,
                f'Evento "{evento.nome}" criado com sucesso!',
                extra_tags='toast'
            )
            return redirect('eventos:detalhe', pk=evento.pk)
        else:
            messages.error(request, 'Verifique os erros no formulário')
    
    form = EventoForm()
    return render(request, 'criar_evento.html', {'form': form})
```

```html
<!-- criar_evento.html -->
{% extends 'base.html' %}

{% block content %}
  {% include 'usuarios/components/toast.html' %}
  {% include 'usuarios/components/messages.html' %}
  
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button>Criar Evento</button>
  </form>
{% endblock %}
```

---

## ✅ Checklist de Implementação

- ✅ Toast.html criado com sistema completo
- ✅ Messages.html criado para integração Django
- ✅ Todas as páginas com {% include %}
- ✅ Login/Logout com notificações
- ✅ Registro com notificações
- ✅ Validação de erros com notificações
- ✅ Responsivo para mobile
- ✅ Animações suaves
- ✅ Material Design Icons

---

## 🚀 Próximos Passos

1. Testar em diferentes navegadores
2. Customizar cores conforme brand
3. Adicionar sons (opcional)
4. Criar eventos de ação nos toasts (opcional)

Pronto para usar! 🎉
