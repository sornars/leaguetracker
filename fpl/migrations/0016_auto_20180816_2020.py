# Generated by Django 2.1 on 2018-08-16 20:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fpl', '0015_auto_20180816_1958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manager',
            name='entrant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
