# Generated by Django 2.1.2 on 2021-02-01 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kallisticore', '0019_auto_20201230_1554'),
    ]

    operations = [
        migrations.AddField(
            model_name='trial',
            name='initiated_from',
            field=models.CharField(default='unknown', max_length=20),
        ),
    ]
