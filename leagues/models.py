from django.db import models


class LeagueType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class League(models.Model):
    name = models.CharField(max_length=50)
    league_type = models.ForeignKey(LeagueType, on_delete=models.PROTECT)

    def __str__(self):
        return self.name
