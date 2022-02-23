# Generated by Django 2.1.2 on 2019-06-18 05:56

from django.db import migrations
import kallisticore.utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('kallisticore', '0009_trialschedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='metadata',
            field=kallisticore.utils.fields.DictField(blank=True, default={}),
        ),
        migrations.AddField(
            model_name='trial',
            name='metadata',
            field=kallisticore.utils.fields.DictField(blank=True, default={}),
        ),
        migrations.AddField(
            model_name='trialschedule',
            name='metadata',
            field=kallisticore.utils.fields.DictField(blank=True, default={}),
        ),
    ]