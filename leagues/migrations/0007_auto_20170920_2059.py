# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-20 20:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0006_auto_20170920_2000'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='league',
            name='league_type',
        ),
        migrations.DeleteModel(
            name='LeagueType',
        ),
    ]