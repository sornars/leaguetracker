import datetime
import requests
from django.conf import settings
from django.db import models
from django.utils.dateparse import parse_datetime


from leagues.models import League, Payout as LeaguePayout


BASE_URL = 'https://fantasy.premierleague.com/drf/'


class ClassicLeague(models.Model):
    league = models.OneToOneField(League, on_delete=models.CASCADE)
    fpl_league_id = models.IntegerField(unique=True)

    def retrieve_league_data(self):
        response = requests.get(
            BASE_URL + 'leagues-classic-standings/{fpl_league_id}'.format(
                fpl_league_id=self.fpl_league_id
            )
        )
        data = response.json()
        self.league.name = data['league']['name']
        self.league.save()
        for manager in data['standings']['results']:
            manager, _ = Manager.objects.update_or_create(
                fpl_manager_id=manager['entry'],
                defaults={
                    'team_name': manager['entry_name']
                }
            )
            manager.retrieve_performance_data()

    def __str__(self):
        return self.league.name

class Manager(models.Model):
    entrant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    team_name = models.CharField(max_length=50)
    fpl_manager_id = models.IntegerField()

    def retrieve_performance_data(self):
        response = requests.get(
            BASE_URL + 'entry/{fpl_manager_id}/history'.format(
                fpl_manager_id=self.fpl_manager_id
            )
        )
        data = response.json()
        for gameweek in data['history']:
            manager_performance, _ = ManagerPerformance.objects.update_or_create(
                manager=self,
                gameweek=Gameweek.objects.get(number=gameweek['event']),
                defaults={
                    'score': gameweek['points'] - gameweek['event_transfers_cost']
                }
            )


    def __str__(self):
        return '{team_name} - {entrant}'.format(team_name=self.team_name, entrant=self.entrant)


class Gameweek(models.Model):
    number = models.IntegerField(unique=True)
    start_date = models.DateField()

    @staticmethod
    def retrieve_gameweek_data():
        response = requests.get(BASE_URL + 'bootstrap-static')
        data = response.json()
        for event in data['events']:
            gameweek, _ = Gameweek.objects.update_or_create(
                number=event['id'],
                defaults={
                    'start_date': parse_datetime(event['deadline_time'])
                }
            )

    def __str__(self):
        return 'Gameweek {number} ({start_date})'.format(
            number=self.number,
            start_date=self.start_date
        )


class ManagerPerformance(models.Model):
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)
    score = models.IntegerField()

    def __str__(self):
        return '{manager} - {gameweek}: {score}'.format(
            manager=self.manager,
            gameweek=self.gameweek,
            score=self.score
        )

    class Meta:
        unique_together = ('manager', 'gameweek')

class Payout(LeaguePayout):

    def calculate_winner(self):
        managers = Manager.objects.filter(
            entrant__league=self.league,
            managerperformance__gameweek__start_date__range=[self.start_date, self.end_date]
        ).annotate(
            score=models.Sum('managerperformance__score')
        ).order_by('-score')

        self.winner = managers[0].entrant
        self.save()

    class Meta:
        proxy = True