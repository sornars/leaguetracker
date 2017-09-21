# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-20 21:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leagues', '0007_auto_20170920_2059'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassicLeague',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fpl_league_id', models.IntegerField()),
                ('league', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='leagues.League')),
            ],
        ),
        migrations.CreateModel(
            name='Manager',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team_name', models.CharField(max_length=50)),
                ('fpl_manager_id', models.IntegerField()),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]