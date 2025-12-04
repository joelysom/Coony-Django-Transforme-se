from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0011_evento_favorited_by_alter_evento_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="gm_permission_level",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
