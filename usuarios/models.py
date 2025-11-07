from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Usuario(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    modalidades = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

    def set_password(self, raw_password):
        """Hash and set the password for this user."""
        self.senha = make_password(raw_password)

    def check_password(self, raw_password):
        """Return True if the given raw_password matches the stored hashed password."""
        return check_password(raw_password, self.senha)
