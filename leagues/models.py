from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import models


class LeagueType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class League(models.Model):
    name = models.CharField(max_length=50)
    league_type = models.ForeignKey(LeagueType, on_delete=models.CASCADE)
    managers = models.ManyToManyField(User, blank=True, through='LeagueEntrant')
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class LeagueEntrant(models.Model):
    manager = models.ForeignKey(User, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    paid_entry = models.BooleanField()

    def __str__(self):
        return '{league} - {manager}'.format(
            league=self.league,
            manager=self.manager
        )

    class Meta:
        unique_together = ('manager', 'league')
