import decimal
import itertools

import requests
from django.conf import settings
from django.db import models, transaction
from django.utils.dateparse import parse_datetime

from leagues.models import League, Payout as LeaguePayout

BASE_URL = 'https://fantasy.premierleague.com/drf/'


class FPLLeague(models.Model):
    league = models.OneToOneField(League, on_delete=models.CASCADE)
    fpl_league_id = models.IntegerField(unique=True)

    def retrieve_league_data(self):
        raise NotImplementedError

    def __str__(self):
        return self.league.name


class ClassicLeague(models.Model):
    fpl_league = models.OneToOneField(FPLLeague, on_delete=models.CASCADE)

    def retrieve_league_data(self):
        response = requests.get(
            BASE_URL + 'leagues-classic-standings/{fpl_league_id}'.format(
                fpl_league_id=self.fpl_league_id
            )
        )
        data = response.json()
        self.fpl_league.league.name = data['league']['name']
        self.fpl_league.league.save()
        for manager in data['standings']['results']:
            manager, _ = Manager.objects.update_or_create(
                fpl_manager_id=manager['entry'],
                defaults={
                    'team_name': manager['entry_name']
                }
            )
            manager.retrieve_performance_data()


class HeadToHeadLeague(models.Model):
    fpl_league = models.OneToOneField(FPLLeague, on_delete=models.CASCADE)

    # TODO: Remove redundancy with ClassicLeague
    def retrieve_league_data(self):
        response = requests.get(
            BASE_URL + 'leagues-h2h-standings/{fpl_league_id}'.format(
                fpl_league_id=self.fpl_league_id
            )
        )
        data = response.json()
        self.fpl_league.league.name = data['league']['name']
        self.fpl_league.league.save()
        for manager in data['standings']['results']:
            manager, _ = Manager.objects.update_or_create(
                fpl_manager_id=manager['entry'],
                defaults={
                    'team_name': manager['entry_name']
                }
            )
            manager.retrieve_performance_data()

        for match in itertools.chain(
                data['matches_this']['results'], data['matches_next']['results']
        ):
            manager_1 = Manager.objects.get(fpl_manager_id=match['entry_1_entry'])
            manager_2 = Manager.objects.get(fpl_manager_id=match['entry_2_entry'])
            h2h_match, _ = HeadToHeadMatch.objects.update_or_create(
                fpl_match_id=match['id'],
                h2h_league=self,
                gameweek=Gameweek.objects.get(number=match['event'])
            )
            h2h_match.participants.add(manager_1, manager_2)
            h2h_match.save()
            h2h_match.calculate_score()


class Manager(models.Model):
    entrant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    team_name = models.CharField(max_length=50)
    fpl_manager_id = models.IntegerField(unique=True)

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


class HeadToHeadMatch(models.Model):
    fpl_match_id = models.IntegerField(unique=True)
    h2h_league = models.ForeignKey(HeadToHeadLeague, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)
    participants = models.ManyToManyField(Manager)

    @transaction.atomic
    def calculate_score(self):
        # Assumes only two participants in a HeadToHeadMatch
        manager_1, manager_2 = self.participants.all().filter(managerperformance__gameweek=self.gameweek).annotate(
            score=models.Sum('managerperformance__score'))

        if manager_1.score == manager_2.score:
            manager_1_score = 1
            manager_2_score = 1
        elif manager_1.score > manager_2.score:
            manager_1_score = 3
            manager_2_score = 0
        else:
            manager_1_score = 0
            manager_2_score = 3

        HeadToHeadPerformance.objects.update_or_create(h2h_league=self.h2h_league,
                                                       manager=manager_1,
                                                       gameweek=self.gameweek,
                                                       defaults={
                                                           'score': manager_1_score
                                                       })
        HeadToHeadPerformance.objects.update_or_create(h2h_league=self.h2h_league,
                                                       manager=manager_2,
                                                       gameweek=self.gameweek,
                                                       defaults={
                                                           'score': manager_2_score
                                                       })


class HeadToHeadPerformance(models.Model):
    h2h_league = models.ForeignKey(HeadToHeadLeague, on_delete=models.CASCADE)
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE)
    gameweek = models.ForeignKey(Gameweek, on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = ('h2h_league', 'manager', 'gameweek')


class Payout(LeaguePayout):
    @transaction.atomic
    def calculate_winner(self):
        managers = Manager.objects.filter(
            entrant__league=self.league,
            managerperformance__gameweek__start_date__range=[self.start_date, self.end_date]
        ).annotate(
            score=models.Sum('managerperformance__score')
        ).order_by(
            '-score'
        )
        # TODO: Move processing to DB with a window function in Django 2.0
        current_rank = {
            'rank': 0,
            'score': None
        }
        for manager in managers:
            if manager.score != current_rank['score']:
                current_rank['rank'] += 1
                current_rank['score'] = manager.score

            manager.rank = current_rank['rank']

        related_payouts = Payout.objects.filter(
            league=self.league,
            start_date=self.start_date,
            end_date=self.end_date
        ).exclude(
            position=self.position
        ).order_by(
            'position'
        )

        for payout in itertools.chain(related_payouts, [self]):
            payout.winning_managers = [manager for manager in managers if manager.rank == payout.position]
            if len(payout.winning_managers) > 1 and related_payouts:
                raise NotImplementedError(
                    'Payouts with multiple positions involving ties must be manually resolved'
                )

        future_payouts = Payout.objects.filter(
            league=self.league,
            position=self.position,
            start_date__gt=self.end_date
        ).order_by(
            'start_date'
        )

        if len(self.winning_managers) > 1 and future_payouts:
            next_payment = future_payouts[0]
            next_payment.amount = models.F('amount') + self.amount
            next_payment.save()
            self.delete()
        else:
            adjusted_payout = round(decimal.Decimal(self.amount) / decimal.Decimal(len(self.winning_managers)), 2)
            remainder = self.amount - (adjusted_payout * len(self.winning_managers))
            self.amount = adjusted_payout + remainder
            self.winner = self.winning_managers[0].entrant
            self.save()

            for winning_manager in self.winning_managers[1:]:
                self.pk = None
                self.amount = adjusted_payout
                self.winner = winning_manager.entrant
                self.save()

    class Meta:
        proxy = True
