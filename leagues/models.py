from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class League(models.Model):
    name = models.CharField(max_length=50)
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


class Payout(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    paid_out = models.BooleanField()
    paid_to = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return '{league} - {name}: {amount}'.format(
            league=self.league,
            name=self.name,
            amount=self.amount
        )

    class Meta:
        abstract = True

class PeriodPayout(Payout):
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('league', 'name', 'start_date', 'end_date')


class PositionPayout(Payout):
    position = models.IntegerField()

    class Meta:
        unique_together = ('league', 'name', 'position')
