# Generated by Django 2.0.2 on 2018-08-15 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fpl', '0013_auto_20180516_1232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classicleague',
            name='last_updated',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='gameweek',
            name='number',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='headtoheadleague',
            name='last_updated',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]