import datetime
import decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from fpl.models import (FPLLeague, ClassicLeague, HeadToHeadLeague, HeadToHeadMatch, Gameweek,
                        Manager, ManagerPerformance, Payout)
from leagues.models import League, LeagueEntrant


class FPLLeagueTestCase(TestCase):
    def test_retrieve_league_data(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        entrant_2 = User.objects.create(username='entrant_2')
        entrant_3 = User.objects.create(username='entrant_3')
        league = League.objects.create(name='Test League', entry_fee=10)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        fpl_league = FPLLeague.objects.create(league=league, fpl_league_id=1)

        with self.assertRaises(NotImplementedError):
            fpl_league.retrieve_league_data()


class ClassicLeagueTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        entrant_2 = User.objects.create(username='entrant_2')
        entrant_3 = User.objects.create(username='entrant_3')
        league = League.objects.create(name='Test League', entry_fee=10)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        fpl_league = FPLLeague.objects.create(league=league, fpl_league_id=1)
        ClassicLeague.objects.create(fpl_league=fpl_league)
        Manager.objects.bulk_create([
            Manager(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1),
            Manager(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2),
            Manager(entrant=entrant_3, team_name='Team 3', fpl_manager_id=3)
        ])

    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.requests.get')
    def test_retrieve_league_data(self, mock_requests_get, _):
        league_data = {
            'league': {
                'name': 'Test League 1'
            },
            'standings': {
                'results': [
                    {
                        'entry': 1,
                        'entry_name': 'Test Manager Team'
                    },
                    {
                        'entry': 2,
                        'entry_name': 'Team 2'
                    },
                    {
                        'entry': 3,
                        'entry_name': 'Team 3'
                    },
                    {
                        'entry': 4,
                        'entry_name': 'Team 4'
                    },
                ]
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = league_data
        mock_requests_get.return_value = mock_response

        classic_league = ClassicLeague.objects.get()
        classic_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 4)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Test Manager Team')
        self.assertEqual(League.objects.get().name, 'Test League 1')


class HeadToHeadLeagueTestCase(TestCase):
    @patch('fpl.models.HeadToHeadMatch.calculate_score')
    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.requests.get')
    def test_retrieve_league_data(self, mock_requests_get, *_):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        entrant_2 = User.objects.create(username='entrant_2')
        entrant_3 = User.objects.create(username='entrant_3')
        league = League.objects.create(name='Test League', entry_fee=10)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        fpl_league = FPLLeague.objects.create(league=league, fpl_league_id=1)
        HeadToHeadLeague.objects.create(fpl_league=fpl_league)
        Manager.objects.bulk_create([
            Manager(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1),
            Manager(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2),
            Manager(entrant=entrant_3, team_name='Team 3', fpl_manager_id=3)
        ])
        Gameweek.objects.create(number=1, start_date='2017-08-01')
        Gameweek.objects.create(number=2, start_date='2017-08-08')
        Gameweek.objects.create(number=3, start_date='2017-08-15')
        league_data = {
            'league': {
                'name': 'Test League 1'
            },
            'standings': {
                'results': [
                    {
                        'entry': 1,
                        'entry_name': 'Test Manager Team'
                    },
                    {
                        'entry': 2,
                        'entry_name': 'Team 2'
                    },
                    {
                        'entry': 3,
                        'entry_name': 'Team 3'
                    },
                    {
                        'entry': 4,
                        'entry_name': 'Team 4'
                    },
                ]
            },
            'matches_this': {
                'results': [
                    {
                        'id': 1,
                        'event': 1,
                        'entry_1_entry': 1,
                        'entry_2_entry': 2
                    },
                    {
                        'id': 2,
                        'event': 2,
                        'entry_1_entry': 1,
                        'entry_2_entry': 3
                    }
                ]
            },
            'matches_next': {
                'results': [
                    {
                        'id': 3,
                        'event': 3,
                        'entry_1_entry': 1,
                        'entry_2_entry': 4
                    }
                ]

            }
        }
        mock_response = Mock()
        mock_response.json.return_value = league_data
        mock_requests_get.return_value = mock_response

        h2h_league = HeadToHeadLeague.objects.get()
        h2h_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 4)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Test Manager Team')
        self.assertEqual(League.objects.get().name, 'Test League 1')
        self.assertEqual(HeadToHeadMatch.objects.count(), 3)



class ManagerTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01')
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08')
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_1, score=0)

    @patch('fpl.models.requests.get')
    def test_retrieve_performance_data(self, mock_requests_get):
        performance_data = {
            'history': [
                {
                    'event': 1,
                    'points': 10,
                    'event_transfers_cost': 0
                },
                {
                    'event': 2,
                    'points': 10,
                    'event_transfers_cost': 8
                }
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = performance_data
        mock_requests_get.return_value = mock_response

        manager = Manager.objects.get()
        manager.retrieve_performance_data()

        self.assertEqual(ManagerPerformance.objects.count(), 2)
        self.assertEqual(
            ManagerPerformance.objects.get(
                manager=manager,
                gameweek=Gameweek.objects.get(number=1)
            ).score,
            10
        )
        self.assertEqual(
            ManagerPerformance.objects.get(
                manager=manager,
                gameweek=Gameweek.objects.get(number=2)
            ).score,
            2
        )


class GameweekTestCase(TestCase):
    def setUp(self):
        Gameweek.objects.create(number=1, start_date='2017-08-01')

    @patch('fpl.models.requests.get')
    def test_retrieve_gameweek_data(self, mock_requests_get):
        gameweek_data = {
            'events': [
                {
                    'id': 1,
                    'deadline_time': '2017-08-11T17:45:00Z'
                },
                {
                    'id': 2,
                    'deadline_time': '2017-08-18T17:45:00Z'
                }
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = gameweek_data
        mock_requests_get.return_value = mock_response

        Gameweek.retrieve_gameweek_data()

        self.assertEqual(Gameweek.objects.count(), 2)
        self.assertEqual(Gameweek.objects.get(number=1).start_date, datetime.date(2017, 8, 11))
        self.assertEqual(Gameweek.objects.get(number=2).start_date, datetime.date(2017, 8, 18))


class PayoutTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.entrant_1 = User.objects.create(username='entrant_1')
        self.entrant_2 = User.objects.create(username='entrant_2')
        self.entrant_3 = User.objects.create(username='entrant_3')
        self.league = League.objects.create(name='Test League', entry_fee=10)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=self.league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_2, league=self.league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_3, league=self.league, paid_entry=True)
        ])
        self.manager_1 = Manager.objects.create(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1)
        self.manager_2 = Manager.objects.create(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2)
        self.manager_3 = Manager.objects.create(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01')
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_1, score=0),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_1, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_1, score=0),
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_2, score=0),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_2, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_2, score=30)
        ])

    def test_calculate_winner_single_winner(self):
        payout_1 = Payout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        Payout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-09-01',
            end_date='2017-09-30',
            paid_out=False
        )
        payout_1.calculate_winner()

        self.assertEqual(payout_1.winner, self.entrant_3)

    def test_calculate_winner_single_winner_tie_with_no_future_payout(self):
        payout = Payout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_3, score=30),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_3, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        payout.calculate_winner()

        payout_1, payout_2, payout_3 = Payout.objects.all()

        self.assertEqual(Payout.objects.count(), 3)
        self.assertEqual(payout_1.amount, decimal.Decimal('3.34'))
        self.assertEqual(payout_2.amount, decimal.Decimal('3.33'))
        self.assertEqual(payout_3.amount, decimal.Decimal('3.33'))

    def test_calculate_single_winner_tie_with_future_payout(self):
        payout_1 = Payout.objects.create(
            league=self.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        Payout.objects.create(
            league=self.league,
            name='Test Payout 2',
            amount=10,
            position=1,
            start_date='2017-09-01',
            end_date='2017-09-30',
            paid_out=False
        )

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_3, score=30),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_3, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        payout_1.calculate_winner()

        self.assertEqual(Payout.objects.count(), 1)
        payout = Payout.objects.get()
        self.assertEqual(payout.amount, 20)

    def test_calculate_multiple_positions_tie(self):
        payout_1 = Payout.objects.create(
            league=self.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        payout_2 = Payout.objects.create(
            league=self.league,
            name='Test Payout 2',
            amount=10,
            position=2,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_3, score=20),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_3, score=0),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        with self.assertRaises(NotImplementedError):
            payout_1.calculate_winner()

        with self.assertRaises(NotImplementedError):
            payout_2.calculate_winner()
