from django.db import migrations, models
from django.utils import timezone


def seed_like_events(apps, schema_editor):
    PostLikeEvent = apps.get_model('usuarios', 'PostLikeEvent')
    connection = schema_editor.connection
    table_name = 'usuarios_post_likes'

    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT post_id, usuario_id FROM {table_name}')
            rows = cursor.fetchall()
    except Exception:
        rows = []

    if not rows:
        return

    now = timezone.now()
    events = []
    seen = set()
    for post_id, usuario_id in rows:
        key = (post_id, usuario_id)
        if key in seen:
            continue
        seen.add(key)
        events.append(PostLikeEvent(post_id=post_id, usuario_id=usuario_id, created_at=now))

    if events:
        PostLikeEvent.objects.bulk_create(events, ignore_conflicts=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0007_message_deleted_by_message_deleted_for_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostLikeEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=models.CASCADE, related_name='like_events', to='usuarios.post')),
                ('usuario', models.ForeignKey(on_delete=models.CASCADE, related_name='generated_like_events', to='usuarios.usuario')),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('post', 'usuario')},
            },
        ),
        migrations.RunPython(seed_like_events, noop),
    ]
