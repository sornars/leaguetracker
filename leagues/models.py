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

    def __str__(self):
        return self.team_name


class League(models.Model):
    name = models.CharField(max_length=50)
    league_type = models.ForeignKey(LeagueType, on_delete=models.CASCADE)
    managers = models.ManyToManyField(Manager, blank=True, through='LeagueEntrant')
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Performance(models.Model):
    gameweek = models.IntegerField()
    league_entrant = models.ForeignKey('LeagueEntrant', on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return '{league_entrant} - {gameweek}: {score}'.format(
            league_entrant=self.league_entrant,
            gameweek=self.gameweek,
            score=self.score
        )

    class Meta:
        unique_together = ('gameweek', 'league_entrant')


class LeagueEntrant(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    paid_entry = models.BooleanField()

    def __str__(self):
        return '{league} - {manager}'.format(
            league=self.league,
            manager=self.manager
        )
