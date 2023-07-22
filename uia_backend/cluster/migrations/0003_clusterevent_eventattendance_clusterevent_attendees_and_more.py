# Generated by Django 4.0.10 on 2023-07-17 16:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_delete_userhandle'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cluster', '0002_alter_clusterinvitation_duration'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClusterEvent',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='Last update at')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, default='')),
                ('event_type', models.CharField(choices=[(0, 'Physical'), (1, 'Virtual'), (2, 'Hybrid')], max_length=10)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('status', models.CharField(choices=[(0, 'Awaiting'), (1, 'Ongoing'), (2, 'Cancelled'), (3, 'Expired')], default=0, max_length=10)),
                ('link', models.URLField(blank=True, null=True)),
                ('event_date', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EventAttendance',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='Last update at')),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'Invited'), (1, 'Attending'), (2, 'Not Attending')], default=0)),
                ('attendee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cluster.clusterevent')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='clusterevent',
            name='attendees',
            field=models.ManyToManyField(related_name='attended_events', through='cluster.EventAttendance', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='clusterevent',
            name='cluster',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cluster.cluster'),
        ),
        migrations.AddField(
            model_name='clusterevent',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
        ),
    ]
