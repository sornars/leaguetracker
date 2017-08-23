# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-23 21:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='LeagueMembership',
            new_name='LeagueEntrant',
        ),
        migrations.RenameField(
            model_name='performance',
            old_name='league_membership',
            new_name='league_entrant',
        ),
        migrations.AlterUniqueTogether(
            name='performance',
            unique_together=set([('gameweek', 'league_entrant')]),
        ),
    ]
