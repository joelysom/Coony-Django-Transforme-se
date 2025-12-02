from django.db import migrations, models
from django.utils.text import slugify
import random
import string


def generate_username(base):
    slug = slugify(base or '') or 'usuario'
    slug = slug[:40].rstrip('-') or 'usuario'
    digits = string.digits
    suffix = ''.join(random.choices(digits, k=6))
    return f"{slug}-{suffix}"


def seed_usernames(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    for user in Usuario.objects.all():
        attempt = 0
        username = None
        while attempt < 25:
            candidate = generate_username(user.nome)
            if not Usuario.objects.filter(username=candidate).exists():
                username = candidate
                break
            attempt += 1
        if username is None:
            username = generate_username('usuario')
        user.username = username[:60]
        user.save(update_fields=['username'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_usuario_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='username',
            field=models.SlugField(blank=True, max_length=60, null=True, unique=True),
        ),
        migrations.RunPython(seed_usernames, noop),
        migrations.AlterField(
            model_name='usuario',
            name='username',
            field=models.SlugField(blank=True, max_length=60, unique=True),
        ),
    ]
