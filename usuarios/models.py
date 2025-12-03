import random
import string

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils.text import slugify
from django.utils import timezone

class Usuario(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)
    localizacao = models.CharField(max_length=100, blank=True, null=True)
    modalidades = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)
    username = models.SlugField(max_length=60, unique=True, blank=True)

    def __str__(self):
        return self.nome

    def set_password(self, raw_password):
        """Hash and set the password for this user."""
        self.senha = make_password(raw_password)

    def check_password(self, raw_password):
        """Return True if the given raw_password matches the stored hashed password."""
        return check_password(raw_password, self.senha)

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.generate_unique_username()
        super().save(*args, **kwargs)

    def generate_unique_username(self):
        base = slugify(self.nome or '') or 'usuario'
        base = base[:40].rstrip('-') or 'usuario'
        digits = string.digits
        for _ in range(25):  # Try a few times before fallback
            suffix = ''.join(random.choices(digits, k=6))
            candidate = f'{base}-{suffix}'
            if not Usuario.objects.filter(username=candidate).exclude(pk=self.pk).exists():
                return candidate
        # Fallback in the unlikely event of many collisions
        fallback = ''.join(random.choices(digits, k=10))
        return f'{base}-{fallback}'[:60]

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


class PostLikeEvent(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='like_events')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='generated_like_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('post', 'usuario')

    def __str__(self):
        return f'{self.usuario.nome} curtiu o post {self.post_id}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comments')
    texto = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comentário de {self.autor.nome} em {self.post.id}: {self.texto[:40]}'

    class Meta:
        ordering = ['data_criacao']


class Conversation(models.Model):
    """Representa uma conversa entre dois usuários (estilo WhatsApp)."""

    conversation_key = models.CharField(max_length=64, unique=True)
    participants = models.ManyToManyField(Usuario, related_name='chat_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Conversa {self.conversation_key}'

    @staticmethod
    def build_key(*user_ids):
        normalized = sorted(str(uid) for uid in user_ids if uid)
        return '|'.join(normalized)

    @classmethod
    def get_or_create_private(cls, user_a, user_b):
        key = cls.build_key(user_a.id, user_b.id)
        conversation, created = cls.objects.get_or_create(conversation_key=key)
        if created:
            conversation.participants.add(user_a, user_b)
        else:
            current_ids = conversation.participants.values_list('id', flat=True)
            missing = [u.id for u in (user_a, user_b) if u.id not in current_ids]
            if missing:
                conversation.participants.add(*missing)
        conversation.touch()
        return conversation

    def touch(self):
        self.updated_at = timezone.now()
        self.save(update_fields=['updated_at'])

    def other_participant(self, current_user):
        return self.participants.exclude(pk=current_user.pk).first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='sent_messages')
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    deleted_for = models.ManyToManyField(Usuario, related_name='hidden_messages', blank=True)
    deleted_for_everyone = models.BooleanField(default=False)
    deleted_for_everyone_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        Usuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='messages_deleted_globally'
    )

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Msg {self.autor.nome} -> {self.conversation_id}: {self.texto[:40]}'


class Evento(models.Model):
    criador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='eventos')
    titulo = models.CharField(max_length=120)
    descricao = models.TextField()
    modalidade = models.CharField(max_length=60)
    nivel_dificuldade = models.CharField(max_length=60, blank=True)
    data = models.DateField()
    hora = models.TimeField()
    local = models.CharField(max_length=120)
    distancia = models.CharField(max_length=40, blank=True)
    max_participantes = models.PositiveIntegerField(null=True, blank=True)
    imagem_capa = models.ImageField(upload_to='eventos/capa/', blank=True)
    favorited_by = models.ManyToManyField('Usuario', related_name='favorited_eventos', blank=True)
    imagem_detalhe_1 = models.ImageField(upload_to='eventos/detalhes/', blank=True)
    imagem_detalhe_2 = models.ImageField(upload_to='eventos/detalhes/', blank=True)
    imagem_detalhe_3 = models.ImageField(upload_to='eventos/detalhes/', blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-hora', '-criado_em']

    def __str__(self):
        return f'{self.titulo} - {self.data:%d/%m/%Y}'
