# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-21 13:56
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0008_auto_20170921_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payout',
            name='paid_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
