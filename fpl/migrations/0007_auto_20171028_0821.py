# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-28 08:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('fpl', '0006_auto_20171028_0757'),
    ]

    operations = [
        migrations.RenameField(
            model_name='headtoheadperformance',
            old_name='league',
            new_name='h2h_league',
        ),
        migrations.AlterField(
            model_name='manager',
            name='fpl_manager_id',
            field=models.IntegerField(unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='headtoheadperformance',
            unique_together=set([('h2h_league', 'manager', 'gameweek')]),
        ),
    ]
