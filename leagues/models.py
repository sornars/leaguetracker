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
    leagues_paid = models.ManyToManyField('League', blank=True)

    def __str__(self):
        self.team_name


class League(models.Model):
    name = models.CharField(max_length=50)
    league_type = models.ForeignKey(LeagueType, on_delete=models.PROTECT)
    managers = models.ManyToManyField(Manager, blank=True)
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class ManagerLeaguePerformance(models.Model):
    gameweek = models.IntegerField()
    manager = models.ForeignKey(Manager, on_delete=models.PROTECT)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return '{manager} - {league} - {gamewweek}: {score}'.format(
            manager=self.manager,
            league=self.league,
            gameweek=self.gameweek,
            score=self.score
        )

    class Meta:
        unique_together = ('gameweek', 'manager', 'league',)
