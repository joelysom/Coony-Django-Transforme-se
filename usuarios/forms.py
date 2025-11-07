from django import forms
from .models import Usuario

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

    def add_error(self, field, error):
        if not field:  # For non-field errors
            self._errors.setdefault('__all__', self.error_class())
            self._errors['__all__'].append(error)
        else:
            super().add_error(field, error)
