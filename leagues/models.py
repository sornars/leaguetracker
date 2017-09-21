from django.conf import settings
from django.db import models


class League(models.Model):
    name = models.CharField(max_length=50)
    managers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, through='LeagueEntrant')
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class LeagueEntrant(models.Model):
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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
    position = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    paid_out = models.BooleanField()
    paid_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return '{league} - {name}: {amount}'.format(
            league=self.league,
            name=self.name,
            amount=self.amount
        )

    class Meta:
        unique_together = ('league', 'name', 'position', 'start_date', 'end_date')
