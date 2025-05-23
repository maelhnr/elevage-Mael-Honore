# Generated by Django 4.2.20 on 2025-04-30 20:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lapin', '0013_alter_individu_sante'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sante',
            name='malade',
        ),
        migrations.AddField(
            model_name='sante',
            name='individu',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sante_individu', to='lapin.individu'),
        ),
        migrations.AlterField(
            model_name='individu',
            name='sante',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='individu_sante', to='lapin.sante'),
        ),
    ]
