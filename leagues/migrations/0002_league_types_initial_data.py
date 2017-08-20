# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def forwards_func(apps, schema_editor):
    LeagueType = apps.get_model('leagues', 'LeagueType')
    db_alias = schema_editor.connection.alias
    LeagueType.objects.using(db_alias).bulk_create([
        LeagueType(name='Draft'),
        LeagueType(name='Classic'),
        LeagueType(name='Head To Head')
    ])

def reverse_func(apps, schema_editor):
    LeagueType = apps.get_model('leagues', 'LeagueType')
    db_alias = schema_editor.connection.alias
    LeagueType.objects.using(db_alias).filter(name='Draft').delete()
    LeagueType.objects.using(db_alias).filter(name='Classic').delete()
    LeagueType.objects.using(db_alias).filter(name='Head To Head').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
