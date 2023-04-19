# Generated by Django 4.0.10 on 2023-04-17 21:15

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailVerification',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='Last update at')),
                ('internal_tracker_id', models.UUIDField(default=uuid.uuid4)),
                ('is_active', models.BooleanField(default=True)),
                ('expiration_date', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.customuser')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
