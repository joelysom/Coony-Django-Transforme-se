from django import forms
from .models import Usuario, Post, Evento

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


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            'titulo',
            'descricao',
            'modalidade',
            'nivel_dificuldade',
            'data',
            'hora',
            'local',
            'distancia',
            'max_participantes',
            'imagem_capa',
            'imagem_detalhe_1',
            'imagem_detalhe_2',
            'imagem_detalhe_3',
        ]
        labels = {
            'titulo': 'Título do Evento',
            'descricao': 'Descrição',
            'modalidade': 'Modalidade Esportiva',
            'nivel_dificuldade': 'Nível de Dificuldade',
            'data': 'Data',
            'hora': 'Hora',
            'local': 'Local',
            'distancia': 'Distância (opcional)',
            'max_participantes': 'Máximo de Participantes (opcional)',
            'imagem_capa': 'Imagem principal (obrigatória)',
            'imagem_detalhe_1': 'Imagem extra 1 (opcional)',
            'imagem_detalhe_2': 'Imagem extra 2 (opcional)',
            'imagem_detalhe_3': 'Imagem extra 3 (opcional)',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Corrida matinal no Marco Zero'}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva seu evento...'}),
            'modalidade': forms.TextInput(attrs={'placeholder': 'Corrida'}),
            'nivel_dificuldade': forms.TextInput(attrs={'placeholder': 'Iniciante, Médio, Avançado...'}),
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
            'local': forms.TextInput(attrs={'placeholder': 'Selecione o local'}),
            'distancia': forms.TextInput(attrs={'placeholder': '5K, 10 milhas, etc.'}),
            'max_participantes': forms.NumberInput(attrs={'placeholder': 'Ex: 20'}),
            'imagem_capa': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'imagem_detalhe_1': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'imagem_detalhe_2': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'imagem_detalhe_3': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def clean_imagem_capa(self):
        imagem = self.cleaned_data.get('imagem_capa')
        if not imagem and not self.instance.pk:
            raise forms.ValidationError('Envie uma imagem principal para o evento.')
        return imagem or self.instance.imagem_capa
