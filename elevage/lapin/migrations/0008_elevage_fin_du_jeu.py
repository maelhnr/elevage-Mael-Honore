# Generated by Django 4.2 on 2025-04-12 23:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lapin", "0007_alter_elevage_tour"),
    ]

    operations = [
        migrations.AddField(
            model_name="elevage",
            name="fin_du_jeu",
            field=models.BooleanField(default=False),
        ),
    ]
