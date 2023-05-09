# Generated by Django 4.0.10 on 2023-05-05 22:51

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailMessageModel',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='Last update at')),
                ('esp', models.CharField(choices=[(0, 'SendInBlue')], default=0, max_length=100)),
                ('internal_tracker_id', models.UUIDField(editable=False)),
                ('message_id', models.CharField(editable=False, max_length=200)),
                ('message_type', models.CharField(blank=True, max_length=100)),
                ('status', models.IntegerField(choices=[(0, 'Pending: Email has been sent to the esp'), (1, 'Sent: Email has been sent by the esp'), (3, 'Success: Email has been delivered to the user'), (4, 'Failed: Emails was not delivered or an error occured')], default=0)),
                ('status_changes', models.JSONField(default=list)),
                ('recipient_email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='EmailTrackingModel',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='Last update at')),
                ('event_timestamp', models.DateTimeField()),
                ('event_type', models.CharField(max_length=200)),
                ('metadata', models.JSONField(default=dict)),
                ('rejection_reason', models.CharField(max_length=100, null=True)),
                ('raw_event_data', models.JSONField(default=dict)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notification.emailmessagemodel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='emailmessagemodel',
            constraint=models.UniqueConstraint(fields=('esp', 'message_id', 'recipient_email'), name='message_id, recipient_email is unique together with esp'),
        ),
    ]
