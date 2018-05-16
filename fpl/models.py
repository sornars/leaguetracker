import itertools

import datetime
import decimal
import requests
from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum, F, Max
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from leagues.models import League, Payout, LeagueEntrant, Season

BASE_URL = 'https://fantasy.premierleague.com/drf/'


class FPLLeague(models.Model):
    league = models.OneToOneField(League, on_delete=models.CASCADE)
    fpl_league_id = models.IntegerField(unique=True)
    last_updated = models.DateTimeField(null=True)

    @property
    def managers(self):
        managers = Manager.objects.filter(
            entrant__leagueentrant__league=self.league
        ).annotate(current_score=Sum('managerperformance__score'),
                   paid_entry=F('entrant__leagueentrant__paid_entry')).order_by('-current_score')

        return managers

    @staticmethod
    def update_last_updated(func):
        def func_wrapper(self):
            output = None
            if datetime.date.today() < self.league.season.end_date + datetime.timedelta(days=14):
                output = func(self)
                self.last_updated = timezone.now()
                self.save()
            return output

        return func_wrapper

    def retrieve_league_data(self):
        raise NotImplementedError

    def _process_payouts(self, payout_proxy):
        final_gameday = Gameweek.objects.filter(season=self.league.season).aggregate(final_gameday=Max('end_date'))[
            'final_gameday']
        Gameweek.retrieve_gameweek_data(self.league.season)
        self.retrieve_league_data()

        most_recent_gameweek_id = Gameweek.objects.filter(
            season=self.league.season,
            end_date__lte=datetime.date.today()
        ).aggregate(models.Max('number'))['number__max']
        most_recent_gameweek = Gameweek.objects.filter(season=self.league.season, number=most_recent_gameweek_id).get()
        unfinalised_payouts = payout_proxy.objects.filter(
            league=self.league,
            end_date__lte=most_recent_gameweek.end_date,
            paid_out=False
        ).order_by('start_date', 'end_date')

        for payout in unfinalised_payouts:
            payout.refresh_from_db()
            payout.calculate_winner()

    @staticmethod
    def get_authorized_session():
        # TODO: Cache cookies
        session = requests.Session()
        session.get('https://fantasy.premierleague.com')
        session.post('https://users.premierleague.com/accounts/login/',
                     data={'csrfmiddlewaretoken': session.cookies['csrftoken'], 'login': settings.FPL_USERNAME,
                           'password': settings.FPL_PASSWORD, 'app': 'plfpl-web',
                           'redirect_uri': 'https://fantasy.premierleague.com/a/login'})

        return session

    def __str__(self):
        return self.league.name

    class Meta:
        abstract = True


class ClassicLeague(FPLLeague):
    def process_payouts(self):
        self._process_payouts(ClassicPayout)

    @FPLLeague.update_last_updated
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
            manager.retrieve_performance_data(self.league.season)


class HeadToHeadLeague(FPLLeague):

    @property
    def managers(self):
        managers = super().managers
        # Can't use annotate again due to https://code.djangoproject.com/ticket/10060
        for manager in managers:
            manager.current_h2h_score = HeadToHeadPerformance.objects.filter(
                manager=manager
            ).aggregate(
                current_h2h_score=Sum('score')
            )['current_h2h_score']
        managers = sorted(managers, key=lambda x: x.current_h2h_score, reverse=True)
        return managers

    def process_payouts(self):
        self._process_payouts(HeadToHeadPayout)

    @transaction.atomic
    @FPLLeague.update_last_updated
    def retrieve_league_data(self):
        data = {
            'matches': {
                'results': []
            }
        }
        has_next = True
        page_number = 1
        session = self.get_authorized_session()
        while has_next:
            response = session.get(
                BASE_URL + 'leagues-entries-and-h2h-matches/league/{fpl_league_id}?page={page_number}'.format(
                    fpl_league_id=self.fpl_league_id,
                    page_number=page_number
                )
            )
            new_data = response.json()
            data['league'] = new_data['league']
            data['league-entries'] = new_data['league-entries']
            data['matches']['results'] = data['matches']['results'] + new_data['matches']['results']
            page_number += 1
            has_next = new_data['matches']['has_next']

        self.league.name = data['league']['name']
        self.league.save()
        for manager in data['league-entries']:
            manager, _ = Manager.objects.update_or_create(
                fpl_manager_id=manager['entry'],
                defaults={
                    'team_name': manager['entry_name']
                }
            )
            manager.retrieve_performance_data(self.league.season)

        for match in data['matches']['results']:
            manager_1 = Manager.objects.get(fpl_manager_id=match['entry_1_entry'])
            manager_2 = Manager.objects.get(fpl_manager_id=match['entry_2_entry'])
            h2h_match, _ = HeadToHeadMatch.objects.update_or_create(
                fpl_match_id=match['id'],
                h2h_league=self,
                gameweek=Gameweek.objects.get(number=match['event'], season=self.league.season),
                manager_1=manager_1,
                manager_2=manager_2
            )
            ManagerPerformance.objects.update_or_create(manager=manager_1, gameweek=h2h_match.gameweek,
                                                        score=match['entry_1_points'])
            ManagerPerformance.objects.update_or_create(manager=manager_2, gameweek=h2h_match.gameweek,
                                                        score=match['entry_2_points'])

        # TODO: Fix redundant query/iteration
        most_recent_gameweek = Gameweek.objects.filter(
            season=self.league.season,
            end_date__lte=datetime.date.today()
        ).aggregate(most_recent_gameweek=models.Max('number'))['most_recent_gameweek']
        completed_h2h_matches = HeadToHeadMatch.objects.filter(gameweek__number__lte=most_recent_gameweek)
        for h2h_match in completed_h2h_matches:
            h2h_match.calculate_score()


class Manager(models.Model):
    entrant = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    team_name = models.CharField(max_length=50)
    fpl_manager_id = models.IntegerField(unique=True)

    def retrieve_performance_data(self, season):
        if datetime.date.today() < season.end_date + datetime.timedelta(days=14):
            response = requests.get(
                BASE_URL + 'entry/{fpl_manager_id}/history'.format(
                    fpl_manager_id=self.fpl_manager_id
                )
            )
            data = response.json()
            for gameweek in data['history']:
                manager_performance, _ = ManagerPerformance.objects.update_or_create(
                    manager=self,
                    gameweek=Gameweek.objects.get(number=gameweek['event'], season=season),
                    defaults={
                        'score': gameweek['points'] - gameweek['event_transfers_cost']
                    }
                )

    def __str__(self):
        return '{team_name} - {entrant}'.format(team_name=self.team_name, entrant=self.entrant)


class Gameweek(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    number = models.IntegerField(unique=True)
    start_date = models.DateField()
    end_date = models.DateField()

    @staticmethod
    def retrieve_gameweek_data(season):
        today = datetime.date.today()
        if season.start_date < today < season.end_date + datetime.timedelta(days=14):
            fixtures_response = requests.get(BASE_URL + 'fixtures')
            fixtures = fixtures_response.json()
            gameweek_end_dates = {}
            for fixture in fixtures:
                if fixture['kickoff_time'] and fixture['event']:
                    end_date = parse_datetime(fixture['kickoff_time']) + datetime.timedelta(days=1)
                    gameweek = fixture['event']
                    if end_date >= gameweek_end_dates.get(gameweek, end_date):
                        gameweek_end_dates[gameweek] = end_date

            response = requests.get(BASE_URL + 'bootstrap-static')
            data = response.json()
            for event in data['events']:
                gameweek, _ = Gameweek.objects.update_or_create(
                    season=season,
                    number=event['id'],
                    defaults={
                        'start_date': parse_datetime(event['deadline_time']),
                        'end_date': gameweek_end_dates[event['id']]
                    }
                )

    def __str__(self):
        return 'Gameweek {number} ({start_date})'.format(
            number=self.number,
            start_date=self.start_date
        )

    class Meta:
        unique_together = ('season', 'number')


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
    manager_1 = models.ForeignKey(Manager, on_delete=models.CASCADE, related_name='+')
    manager_2 = models.ForeignKey(Manager, on_delete=models.CASCADE, related_name='+')

    @transaction.atomic
    def calculate_score(self):
        manager_1_performance = ManagerPerformance.objects.get(manager=self.manager_1, gameweek=self.gameweek).score
        manager_2_performance = ManagerPerformance.objects.get(manager=self.manager_2, gameweek=self.gameweek).score

        if manager_1_performance == manager_2_performance:
            manager_1_score = 1
            manager_2_score = 1
        elif manager_1_performance > manager_2_performance:
            manager_1_score = 3
            manager_2_score = 0
        else:
            manager_1_score = 0
            manager_2_score = 3

        HeadToHeadPerformance.objects.update_or_create(h2h_league=self.h2h_league,
                                                       manager=self.manager_1,
                                                       gameweek=self.gameweek,
                                                       defaults={
                                                           'score': manager_1_score
                                                       })
        HeadToHeadPerformance.objects.update_or_create(h2h_league=self.h2h_league,
                                                       manager=self.manager_2,
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


class FPLPayout(Payout):
    def _calculate_winner(self, managers):
        if not managers:
            raise ValueError('Cannot calculate payout without participating managers')

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
            'start_date', 'end_date'
        )

        if len(self.winning_managers) > 1 and future_payouts:
            next_payment = future_payouts[0]
            next_payment.start_date = self.start_date
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


class ClassicPayout(FPLPayout):
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

        self._calculate_winner(managers)

    class Meta:
        proxy = True


class HeadToHeadPayout(FPLPayout):
    @transaction.atomic
    def calculate_winner(self):
        # TODO: Improve speed
        managers = Manager.objects.filter(
            entrant__league=self.league,
            headtoheadperformance__gameweek__start_date__range=[self.start_date, self.end_date]
        ).annotate(
            score=models.Sum('headtoheadperformance__score')
        ).order_by(
            '-score'
        )

        self._calculate_winner(managers)

    class Meta:
        proxy = True
