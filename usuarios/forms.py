from django import forms
from .models import Usuario, Post

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label='Senha')
    password_confirm = forms.CharField(widget=forms.PasswordInput(), label='Confirmar Senha')

    class Meta:
        model = Usuario
        fields = ['nome', 'telefone', 'email', 'localizacao', 'modalidades', 'bio']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        pwd2 = cleaned.get('password_confirm')
        if pwd and pwd2 and pwd != pwd2:
            self.add_error('password_confirm', 'As senhas não coincidem.')
        return cleaned


class LoginForm(forms.Form):
    email = forms.CharField(label='E-mail ou Usuário')
    password = forms.CharField(widget=forms.PasswordInput(), label='Senha')

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['texto', 'imagem', 'localizacao']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Compartilhe a sua conquista...', 'class': 'share-textarea'}),
            'imagem': forms.ClearableFileInput(attrs={'id': 'photo-input'}),
            'localizacao': forms.TextInput(attrs={'placeholder': 'Adicionar localização (opcional)'}),
        }


class CommentForm(forms.Form):
    texto = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Escreva um comentário...', 'class': 'comment-textarea'}), max_length=1000)
