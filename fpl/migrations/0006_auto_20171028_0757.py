# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-28 07:57
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('fpl', '0005_auto_20171027_1027'),
    ]

    operations = [
        migrations.CreateModel(
            name='HeadToHeadMatch',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fpl_match_id', models.IntegerField(unique=True)),
                ('gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.Gameweek')),
                ('participants', models.ManyToManyField(to='fpl.Manager')),
            ],
        ),
        migrations.CreateModel(
            name='HeadToHeadPerformance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField()),
                ('gameweek', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.Gameweek')),
                ('manager', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.Manager')),
            ],
        ),
        migrations.DeleteModel(
            name='ClassicLeague',
        ),
        migrations.DeleteModel(
            name='HeadToHeadLeague',
        ),
        migrations.CreateModel(
            name='ClassicLeague',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fpl_league', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fpl.FPLLeague')),
            ],
        ),
        migrations.CreateModel(
            name='HeadToHeadLeague',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fpl_league', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='fpl.FPLLeague')),
            ],
        ),
        migrations.AddField(
            model_name='headtoheadperformance',
            name='league',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.HeadToHeadLeague'),
        ),
        migrations.AddField(
            model_name='headtoheadmatch',
            name='h2h_league',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fpl.HeadToHeadLeague'),
        ),
        migrations.AlterUniqueTogether(
            name='headtoheadperformance',
            unique_together=set([('league', 'manager', 'gameweek')]),
        ),
    ]
