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
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)

    def __str__(self):
        return self.nome

    def set_password(self, raw_password):
        """Hash and set the password for this user."""
        self.senha = make_password(raw_password)

    def check_password(self, raw_password):
        """Return True if the given raw_password matches the stored hashed password."""
        return check_password(raw_password, self.senha)

class Post(models.Model):
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='posts')
    texto = models.TextField()
    imagem = models.ImageField(upload_to='posts/', blank=True, null=True)
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(Usuario, related_name='liked_posts', blank=True)

    def __str__(self):
        return f'Post de {self.autor.nome}: {self.texto[:50]}'

    class Meta:
        ordering = ['-data_criacao']


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comments')
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comentário de {self.autor.nome} em {self.post.id}: {self.texto[:40]}'

    class Meta:
        ordering = ['data_criacao']
