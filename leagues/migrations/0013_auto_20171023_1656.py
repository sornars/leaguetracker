# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-23 16:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leagues', '0012_auto_20171003_1559'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='payout',
            unique_together=set([('league', 'position', 'start_date', 'end_date', 'winner')]),
        ),
    ]
