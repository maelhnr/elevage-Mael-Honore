# Generated by Django 4.2 on 2025-04-10 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lapin", "0004_regle"),
    ]

    operations = [
        migrations.AlterField(
            model_name="regle",
            name="conso_2_mois",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Conso en g/mois pour un lapin de 2 mois",
                max_digits=6,
            ),
        ),
        migrations.AlterField(
            model_name="regle",
            name="conso_3_mois_et_plus",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Conso en g/mois à partir de 3 mois",
                max_digits=6,
            ),
        ),
    ]
