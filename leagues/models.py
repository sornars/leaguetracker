from django.conf import settings
from django.db import models


class League(models.Model):
    season = models.ForeignKey('Season', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    entrants = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='LeagueEntrant')
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return '({season}) - {name}'.format(season=self.season, name=self.name)


class LeagueEntrant(models.Model):
    entrant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    paid_entry = models.BooleanField()

    def __str__(self):
        return '{league} - {entrant}'.format(
            league=self.league,
            entrant=self.entrant
        )

    class Meta:
        unique_together = ('entrant', 'league')


class Payout(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    position = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    paid_out = models.BooleanField()

    def calculate_winner(self):
        raise NotImplementedError

    def __str__(self):
        return '{league} - {name} Position {position} ({start_date}-{end_date}): {amount}'.format(
            league=self.league,
            name=self.name,
            position=self.position,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=self.amount
        )

    class Meta:
        unique_together = ('league', 'position', 'start_date', 'end_date', 'winner')


class Season(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return '{start_date} - {end_date}'.format(
            start_date=self.start_date,
            end_date=self.end_date
        )

    class Meta:
        unique_together = ('start_date', 'end_date')
