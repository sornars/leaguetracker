from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import models


class LeagueType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Manager(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    team_name = models.CharField(max_length=50)


class League(models.Model):
    name = models.CharField(max_length=50)
    league_type = models.ForeignKey(LeagueType, on_delete=models.PROTECT)
    managers = models.ManyToManyField(Manager)

    def __str__(self):
        return self.name
