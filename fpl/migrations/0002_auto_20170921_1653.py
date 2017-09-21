# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-21 16:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fpl', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gameweek',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(unique=True)),
                ('start_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='ManagerPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.Gameweek')),
                ('manager', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.Manager')),
            ],
        ),
        migrations.AlterField(
            model_name='classicleague',
            name='fpl_league_id',
            field=models.IntegerField(unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='managerperformance',
            unique_together=set([('manager', 'gameweek')]),
        ),
    ]