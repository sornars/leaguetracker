from django.db import models


class LeagueType(models.Model):
    name = models.CharField(max_length=50)


class League(models.Model):
    name = models.CharField(max_length=50)
    league_type = models.ForeignKey(LeagueType, on_delete=models.PROTECT)
