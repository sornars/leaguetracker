import datetime
import decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from fpl.models import (ClassicLeague, HeadToHeadLeague, HeadToHeadMatch, HeadToHeadPerformance, Gameweek,
                        Manager, ManagerPerformance, ClassicPayout, HeadToHeadPayout)
from leagues.models import League, LeagueEntrant


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
        ClassicLeague.objects.create(league=league, fpl_league_id=1)
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
        self.assertIsNotNone(classic_league.last_updated)


    @patch('fpl.models.ClassicLeague.retrieve_league_data')
    def test_process_payouts(self, _):
        classic_league = ClassicLeague.objects.get()
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-02')
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-09')
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-16')
        payout_1 = ClassicPayout.objects.create(
            league=classic_league.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date=gameweek_1.start_date,
            end_date=gameweek_1.end_date,
            paid_out=False
        )
        payout_2 = ClassicPayout.objects.create(
            league=classic_league.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date=gameweek_2.start_date,
            end_date=gameweek_2.end_date,
            paid_out=False
        )
        payout_3 = ClassicPayout.objects.create(
            league=classic_league.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date=gameweek_3.start_date,
            end_date=gameweek_3.end_date,
            paid_out=False
        )
        manager_1, manager_2, manager_3 = Manager.objects.all()
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_1, score=0)
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_2, score=0)
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_3, score=10)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek_1, score=0)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek_2, score=10)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek_3, score=10)
        ManagerPerformance.objects.create(manager=manager_3, gameweek=gameweek_1, score=0)
        ManagerPerformance.objects.create(manager=manager_3, gameweek=gameweek_2, score=20)
        ManagerPerformance.objects.create(manager=manager_3, gameweek=gameweek_3, score=15)

        classic_league.process_payouts()
        self.assertEqual(ClassicPayout.objects.count(), 2)
        payout_1_processed, payout_2_processed = ClassicPayout.objects.all()
        self.assertEqual(payout_1_processed.amount, 20)
        self.assertEqual(payout_1_processed.start_date,
                         datetime.datetime.strptime(payout_1.start_date, '%Y-%m-%d').date())
        self.assertEqual(payout_1_processed.end_date, datetime.datetime.strptime(payout_2.end_date, '%Y-%m-%d').date())
        self.assertEqual(payout_1_processed.winner, manager_3.entrant)
        self.assertEqual(payout_2_processed.amount, 10)
        self.assertEqual(payout_2_processed.start_date,
                         datetime.datetime.strptime(payout_3.start_date, '%Y-%m-%d').date())
        self.assertEqual(payout_2_processed.end_date, datetime.datetime.strptime(payout_3.end_date, '%Y-%m-%d').date())
        self.assertEqual(payout_2_processed.winner, manager_3.entrant)


class HeadToHeadLeagueTestCase(TestCase):

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
        HeadToHeadLeague.objects.create(league=league, fpl_league_id=1)
        Manager.objects.bulk_create([
            Manager(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1),
            Manager(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2),
            Manager(entrant=entrant_3, team_name='Team 3', fpl_manager_id=3)
        ])
        Gameweek.objects.bulk_create([
            Gameweek(number=1, start_date='2017-08-01', end_date='2017-08-02'),
            Gameweek(number=2, start_date='2017-08-08', end_date='2017-08-09'),
            Gameweek(number=3, start_date='2017-08-15', end_date='2017-08-16')
        ])


    @patch('fpl.models.HeadToHeadMatch.calculate_score')
    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.FPLLeague.get_authorized_session')
    def test_retrieve_league_data(self, mock_get_authorized_session, *_):
        league_data = {
            'league': {
                'name': 'Test League 1'
            },
            'league-entries': [
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
            ],
            'matches': {
                'has_next': False,
                'results': [
                    {
                        'id': 3,
                        'event': 3,
                        'entry_1_entry': 1,
                        'entry_1_points': 10,
                        'entry_2_entry': 4,
                        'entry_2_points': 20
                    },
                    {
                        'id': 4,
                        'event': 3,
                        'entry_1_entry': 2,
                        'entry_1_points': 10,
                        'entry_2_entry': 3,
                        'entry_2_points': 20
                    }
                ]

            }
        }

        mock_response = Mock()
        mock_response.json.return_value = league_data
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_get_authorized_session.return_value = mock_session
        h2h_league = HeadToHeadLeague.objects.get()
        h2h_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 4)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Test Manager Team')
        self.assertEqual(League.objects.get().name, 'Test League 1')
        self.assertEqual(HeadToHeadMatch.objects.count(), 2)
        self.assertIsNotNone(h2h_league.last_updated)

    @patch('fpl.models.HeadToHeadLeague.retrieve_league_data')
    def test_process_payouts(self, _):
        h2h_league = HeadToHeadLeague.objects.get()
        gameweek_1, gameweek_2, gameweek_3 = Gameweek.objects.order_by('start_date').all()
        payout_1 = HeadToHeadPayout.objects.create(
            league=h2h_league.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date=gameweek_1.start_date,
            end_date=gameweek_1.end_date,
            paid_out=False
        )
        payout_2 = HeadToHeadPayout.objects.create(
            league=h2h_league.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date=gameweek_2.start_date,
            end_date=gameweek_2.end_date,
            paid_out=False
        )
        payout_3 = HeadToHeadPayout.objects.create(
            league=h2h_league.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date=gameweek_3.start_date,
            end_date=gameweek_3.end_date,
            paid_out=False
        )
        manager_1, manager_2, manager_3 = Manager.objects.all()
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_1, gameweek=gameweek_1, score=0)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_1, gameweek=gameweek_2, score=0)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_1, gameweek=gameweek_3, score=10)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_2, gameweek=gameweek_1, score=0)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_2, gameweek=gameweek_2, score=10)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_2, gameweek=gameweek_3, score=10)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_3, gameweek=gameweek_1, score=0)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_3, gameweek=gameweek_2, score=20)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league, manager=manager_3, gameweek=gameweek_3, score=15)

        h2h_league.process_payouts()
        self.assertEqual(HeadToHeadPayout.objects.count(), 2)
        payout_1_processed, payout_2_processed = HeadToHeadPayout.objects.all()
        self.assertEqual(payout_1_processed.amount, 20)
        self.assertEqual(payout_1_processed.start_date,
                         payout_1.start_date)
        self.assertEqual(payout_1_processed.end_date, payout_2.end_date)
        self.assertEqual(payout_1_processed.winner, manager_3.entrant)
        self.assertEqual(payout_2_processed.amount, 10)
        self.assertEqual(payout_2_processed.start_date,
                         payout_3.start_date)
        self.assertEqual(payout_2_processed.end_date, payout_3.end_date)
        self.assertEqual(payout_2_processed.winner, manager_3.entrant)


class HeadToHeadMatchTestCase(TestCase):
    def test_calculate_score(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        entrant_2 = User.objects.create(username='entrant_2')
        league = League.objects.create(name='Test League', entry_fee=10)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True)
        ])
        h2h_league = HeadToHeadLeague.objects.create(league=league, fpl_league_id=1)
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1)
        manager_2 = Manager.objects.create(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2)
        gameweek = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03')
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek, score=0)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek, score=10)

        h2h_match = HeadToHeadMatch.objects.create(fpl_match_id=1, h2h_league=h2h_league, gameweek=gameweek,
                                                   manager_1=manager_1, manager_2=manager_2)
        h2h_match.calculate_score()
        self.assertEqual(HeadToHeadPerformance.objects.count(), 2)
        manager_1_h2h_performance = HeadToHeadPerformance.objects.get(manager=manager_1, gameweek=gameweek,
                                                                      h2h_league=h2h_league)
        manager_2_h2h_performance = HeadToHeadPerformance.objects.get(manager=manager_2, gameweek=gameweek,
                                                                      h2h_league=h2h_league)
        self.assertEqual(manager_1_h2h_performance.score, 0)
        self.assertEqual(manager_2_h2h_performance.score, 3)


class ManagerTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03')
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11')
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
        Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03')

    @patch('fpl.models.requests.get')
    def test_retrieve_gameweek_data(self, mock_requests_get):
        fixture_data = [
            {
                "kickoff_time": "2017-08-11T18:45:00Z",
                "event": 1
            }, {

                "kickoff_time": "2017-08-12T11:30:00Z",
                "event": 2
            }
        ]
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
        mock_response.json.side_effect = [fixture_data, gameweek_data]
        mock_requests_get.return_value = mock_response

        Gameweek.retrieve_gameweek_data()

        self.assertEqual(Gameweek.objects.count(), 2)
        self.assertEqual(Gameweek.objects.get(number=1).start_date, datetime.date(2017, 8, 11))
        self.assertEqual(Gameweek.objects.get(number=2).start_date, datetime.date(2017, 8, 18))


class ClassicPayoutTestCase(TestCase):
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
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03')
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_1, score=0),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_1, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_1, score=0),
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_2, score=0),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_2, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_2, score=30)
        ])

    def test_calculate_winner_single_winner(self):
        payout_1 = ClassicPayout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        ClassicPayout.objects.create(
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

    def test_calculate_winner_single_winner_tie_without_future_payout(self):
        payout = ClassicPayout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_3, score=30),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_3, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        payout.calculate_winner()

        payout_1, payout_2, payout_3 = ClassicPayout.objects.all()

        self.assertEqual(ClassicPayout.objects.count(), 3)
        self.assertEqual(payout_1.amount, decimal.Decimal('3.34'))
        self.assertEqual(payout_2.amount, decimal.Decimal('3.33'))
        self.assertEqual(payout_3.amount, decimal.Decimal('3.33'))

    def test_calculate_single_winner_tie_with_future_payout(self):
        payout_1 = ClassicPayout.objects.create(
            league=self.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        ClassicPayout.objects.create(
            league=self.league,
            name='Test Payout 2',
            amount=10,
            position=1,
            start_date='2017-09-01',
            end_date='2017-09-30',
            paid_out=False
        )

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_3, score=30),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_3, score=10),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        payout_1.calculate_winner()

        self.assertEqual(ClassicPayout.objects.count(), 1)
        payout = ClassicPayout.objects.get()
        self.assertEqual(payout.start_date, datetime.datetime.strptime(payout_1.start_date, '%Y-%m-%d').date())
        self.assertEqual(payout.amount, 20)

    def test_calculate_multiple_positions_tie(self):
        payout_1 = ClassicPayout.objects.create(
            league=self.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        payout_2 = ClassicPayout.objects.create(
            league=self.league,
            name='Test Payout 2',
            amount=10,
            position=2,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18')
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=self.manager_1, gameweek=gameweek_3, score=20),
            ManagerPerformance(manager=self.manager_2, gameweek=gameweek_3, score=0),
            ManagerPerformance(manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        with self.assertRaises(NotImplementedError):
            payout_1.calculate_winner()

        with self.assertRaises(NotImplementedError):
            payout_2.calculate_winner()


class HeadToHeadPayoutTestCase(TestCase):
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
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03')
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11')
        self.h2h_league = HeadToHeadLeague.objects.create(league=self.league, fpl_league_id=1)
        HeadToHeadPerformance.objects.bulk_create([
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_1, gameweek=gameweek_1, score=0),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_2, gameweek=gameweek_1, score=1),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_3, gameweek=gameweek_1, score=0),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_1, gameweek=gameweek_2, score=0),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_2, gameweek=gameweek_2, score=1),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_3, gameweek=gameweek_2, score=3)
        ])

    def test_calculate_winner_single_winner(self):
        payout_1 = HeadToHeadPayout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        HeadToHeadPayout.objects.create(
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

    def test_calculate_winner_single_winner_tie_without_future_payout(self):
        payout = HeadToHeadPayout.objects.create(
            league=self.league,
            name='Test Payout',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18')
        HeadToHeadPerformance.objects.bulk_create([
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_1, gameweek=gameweek_3, score=3),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_2, gameweek=gameweek_3, score=1),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        payout.calculate_winner()

        payout_1, payout_2, payout_3 = HeadToHeadPayout.objects.all()

        self.assertEqual(HeadToHeadPayout.objects.count(), 3)
        self.assertEqual(payout_1.amount, decimal.Decimal('3.34'))
        self.assertEqual(payout_2.amount, decimal.Decimal('3.33'))
        self.assertEqual(payout_3.amount, decimal.Decimal('3.33'))

    def test_calculate_single_winner_tie_with_future_payout(self):
        payout_1 = HeadToHeadPayout.objects.create(
            league=self.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        HeadToHeadPayout.objects.create(
            league=self.league,
            name='Test Payout 2',
            amount=10,
            position=1,
            start_date='2017-09-01',
            end_date='2017-09-30',
            paid_out=False
        )

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18')
        HeadToHeadPerformance.objects.bulk_create([
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_1, gameweek=gameweek_3, score=3),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_2, gameweek=gameweek_3, score=1),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        payout_1.calculate_winner()

        self.assertEqual(HeadToHeadPayout.objects.count(), 1)
        payout = HeadToHeadPayout.objects.get()
        self.assertEqual(payout.amount, 20)

    def test_calculate_multiple_positions_tie(self):
        payout_1 = HeadToHeadPayout.objects.create(
            league=self.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )
        payout_2 = HeadToHeadPayout.objects.create(
            league=self.league,
            name='Test Payout 2',
            amount=10,
            position=2,
            start_date='2017-08-01',
            end_date='2017-08-31',
            paid_out=False
        )

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18')
        HeadToHeadPerformance.objects.bulk_create([
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_1, gameweek=gameweek_3, score=2),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_2, gameweek=gameweek_3, score=0),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        with self.assertRaises(NotImplementedError):
            payout_1.calculate_winner()

        with self.assertRaises(NotImplementedError):
            payout_2.calculate_winner()
