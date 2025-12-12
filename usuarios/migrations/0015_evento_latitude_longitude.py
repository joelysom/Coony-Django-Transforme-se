from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0014_empresaprofile_gm_permission_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]
