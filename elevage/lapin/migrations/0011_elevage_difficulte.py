# Generated by Django 4.2.20 on 2025-04-28 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lapin', '0010_individu_sante_alter_sante_individu'),
    ]

    operations = [
        migrations.AddField(
            model_name='elevage',
            name='difficulte',
            field=models.CharField(choices=[('facile', 'Facile'), ('moyen', 'Moyen'), ('difficile', 'Difficile')], default='moyen', max_length=10),
        ),
    ]
