# Generated by Django 2.1.2 on 2018-11-22 01:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('walker_panel', '0002_auto_20181122_0048'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='region',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='walker_panel.City'),
        ),
    ]