# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-23 22:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0002_auto_20170823_2155'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='leagueentrant',
            unique_together=set([('manager', 'league')]),
        ),
    ]
