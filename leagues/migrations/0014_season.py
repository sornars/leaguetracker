# Generated by Django 2.0.2 on 2018-05-15 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0013_auto_20171023_1656'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
    ]
