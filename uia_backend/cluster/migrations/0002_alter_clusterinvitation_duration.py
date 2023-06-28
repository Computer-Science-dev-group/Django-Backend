# Generated by Django 4.0.10 on 2023-06-30 20:18

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cluster", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="clusterinvitation",
            name="duration",
            field=models.PositiveBigIntegerField(
                default=1, help_text="Duration in days."
            ),
        ),
        migrations.AddField(
            model_name="clusterinvitation",
            name="duration",
            field=models.DurationField(
                default=datetime.timedelta(days=1), help_text="Duration in days."
            ),
        ),
    ]
