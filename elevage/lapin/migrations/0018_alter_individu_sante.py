# Generated by Django 4.2.20 on 2025-04-30 20:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lapin', '0017_alter_sante_individu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='individu',
            name='sante',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='individu_sante', to='lapin.sante'),
        ),
    ]
