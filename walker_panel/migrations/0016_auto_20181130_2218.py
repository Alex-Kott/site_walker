# Generated by Django 2.1.2 on 2018-11-30 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('walker_panel', '0015_log_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='delay',
            field=models.IntegerField(default=0),
        ),
    ]
