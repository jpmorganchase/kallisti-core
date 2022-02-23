# Generated by Django 2.1.2 on 2019-06-13 07:41

from django.db import migrations, models
import django.db.models.deletion
import kallisticore.models.trial
import kallisticore.models.trial_schedule
import kallisticore.utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('kallisticore', '0008_trial_records'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrialSchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('parameters', kallisticore.utils.fields.DictField(blank=True, default={})),
                ('ticket', kallisticore.utils.fields.DictField(blank=True, default={}, validators=[kallisticore.models.trial.validate_trial_ticket])),
                ('recurrence_pattern', models.CharField(max_length=20, validators=[kallisticore.models.trial_schedule.validate_recurrence_pattern])),
                ('recurrence_count', models.IntegerField(blank=True, null=True)),
                ('created_by', models.CharField(default='unknown', max_length=7)),
                ('created_at', models.DateTimeField()),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('experiment', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='schedules', to='kallisticore.Experiment')),
                ('trials', models.ManyToManyField(related_name='trial_schedules', to='kallisticore.Trial')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
