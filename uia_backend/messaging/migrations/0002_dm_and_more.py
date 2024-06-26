# Generated by Django 4.0.10 on 2023-08-15 20:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import encrypted_model_fields.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0006_follows_customuser_follows_follows_user_from_and_more'),
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DM',
            fields=[
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created_datetime', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('updated_datetime', models.DateTimeField(auto_now=True, verbose_name='Last update at')),
                ('content', encrypted_model_fields.fields.EncryptedTextField(blank=True, default='')),
                ('edited', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='filemodel',
            name='dm',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='messaging.dm'),
        ),
        migrations.RemoveConstraint(
            model_name='filemodel',
            name='messaging_filemodel Must set one of comment or post.',
        ),
        migrations.AddConstraint(
            model_name='filemodel',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('comment__isnull', True), ('post__isnull', False), ('dm__isnull', True)), models.Q(('comment__isnull', False), ('post__isnull', True), ('dm__isnull', True)), models.Q(('comment__isnull', True), ('post__isnull', True), ('dm__isnull', False)), models.Q(('comment__isnull', True), ('post__isnull', True), ('dm__isnull', True)), _connector='OR'), name='messaging_filemodel Must set one of comment, post, or dm.'),
        ),
        migrations.AddField(
            model_name='dm',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dm',
            name='friendship',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.friendship'),
        ),
        migrations.AddField(
            model_name='dm',
            name='replying',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='messaging.dm'),
        ),
    ]
