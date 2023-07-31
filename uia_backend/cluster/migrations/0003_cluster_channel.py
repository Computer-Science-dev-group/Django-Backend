# Generated by Django 4.0.10 on 2023-07-31 16:46

from django.db import migrations, models
import django.db.models.deletion
from django.db import transaction
from django.conf import settings


def create_channel_for_clusters(apps, schema_editor):
    """Create centrifugo channel table for clusters without channel."""

    Channel = apps.get_model("instant", "Channel")
    Cluster = apps.get_model("cluster", "Cluster")
    db_alias = schema_editor.connection.alias

    with transaction.atomic():
        for cluster in Cluster.objects.using(db_alias).all():
            if cluster.internal_cluster:
                channel=Channel.objects.using(db_alias).create(
                    name=f'{settings.PUBLIC_CLUSTER_NAMESPACE}:{cluster.title.lower().replace(" ", "")}',
                    level='public',
                )
                cluster.channel = channel
            else:
                channel, created=Channel.objects.using(db_alias).get_or_create(
                    name=f'{settings.PRIVATE_CLUSTER_NAMESPACE}:{cluster.id}',
                    level='users',
                )

                if created:
                    cluster.channel = channel
            cluster.save()

class Migration(migrations.Migration):

    dependencies = [
        ('instant', '0002_alter_channel_level'),
        ('cluster', '0002_alter_clusterinvitation_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='channel',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='instant.channel'),
        ),
        migrations.RunPython(code=create_channel_for_clusters, atomic=True),
        migrations.AlterField(
            model_name='cluster',
            name='channel',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='instant.channel'),
        ),
    ]
