import datetime
import decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import Mock, patch

from fpl.models import (ClassicLeague, HeadToHeadLeague, HeadToHeadMatch, HeadToHeadPerformance, Gameweek,
                        Manager, ManagerPerformance, ClassicPayout, HeadToHeadPayout)
from leagues.models import League, LeagueEntrant, Season


class ClassicLeagueTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.entrant_1 = User.objects.create(username='entrant_1')
        self.entrant_2 = User.objects.create(username='entrant_2')
        self.entrant_3 = User.objects.create(username='entrant_3')
        season = Season.objects.create(start_date='2018-08-01', end_date='2018-05-15')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_3, league=league, paid_entry=True)
        ])
        ClassicLeague.objects.create(league=league, fpl_league_id=1)
        Manager.objects.bulk_create([
            Manager(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1, season=season),
            Manager(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2, season=season),
            Manager(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3, season=season)
        ])


    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.datetime')
    @patch('fpl.models.requests.get')
    def test_retrieve_league_data(self, mock_requests_get, mock_datetime, _):
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
        mock_datetime.date.today.return_value = datetime.date(2018, 5, 10)
        mock_datetime.timedelta.side_effect = lambda *args, **kw: datetime.timedelta(*args, **kw)

        classic_league = ClassicLeague.objects.get()
        classic_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 4)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Test Manager Team')
        self.assertEqual(League.objects.get().name, 'Test League 1')
        self.assertIsNotNone(classic_league.last_updated)

    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.requests.get')
    def test_retrieve_league_data_after_season_end_does_not_update(self, mock_requests_get, _):
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
        today = datetime.date.today()
        season = Season.objects.create(start_date='2018-08-01', end_date=today - datetime.timedelta(days=14))
        classic_league.league.season = season
        classic_league.league.save()
        classic_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 3)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Team 1')
        self.assertEqual(League.objects.get().name, 'Test League')
        self.assertIsNone(classic_league.last_updated)

        mock_requests_get.assert_not_called()

    @patch('fpl.models.Gameweek.retrieve_gameweek_data')
    @patch('fpl.models.ClassicLeague.retrieve_league_data')
    def test_process_payouts(self, mock_retrieve_league_data, mock_retrieve_gameweek_data):
        classic_league = ClassicLeague.objects.get()
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-02',
                                             season=classic_league.league.season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-09',
                                             season=classic_league.league.season)
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-16',
                                             season=classic_league.league.season)
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
        mock_retrieve_gameweek_data.assert_called_once()
        mock_retrieve_league_data.assert_called_once()
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

    def test_managers(self):
        classic_league = ClassicLeague.objects.get()
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-02',
                                             season=classic_league.league.season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-09',
                                             season=classic_league.league.season)
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-16',
                                             season=classic_league.league.season)

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

        self.assertEqual(len(classic_league.managers), 3)
        self.assertEqual(classic_league.managers[0].current_score, 35)
        self.assertEqual(classic_league.managers[1].current_score, 20)
        self.assertEqual(classic_league.managers[2].current_score, 10)
        self.assertTrue(classic_league.managers[0].paid_entry)
        self.assertTrue(classic_league.managers[1].paid_entry)
        self.assertTrue(classic_league.managers[2].paid_entry)

        season_2 = Season.objects.create(start_date='2019-08-01', end_date='2019-05-15')
        Manager.objects.bulk_create([
            Manager(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1, season=season_2),
            Manager(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2, season=season_2),
            Manager(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3, season=season_2)
        ])

        league_2 = League.objects.create(name='Test League 2', entry_fee=10, season=season_2)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=league_2, paid_entry=False),
            LeagueEntrant(entrant=self.entrant_2, league=league_2, paid_entry=False),
            LeagueEntrant(entrant=self.entrant_3, league=league_2, paid_entry=False)
        ])
        classic_league_2 = ClassicLeague.objects.create(league=league_2, fpl_league_id=1)

        gameweek_4 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-02',
                                             season=classic_league_2.league.season)
        gameweek_5 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-09',
                                             season=classic_league_2.league.season)
        gameweek_6 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-16',
                                             season=classic_league_2.league.season)

        manager_1, manager_2, manager_3 = Manager.objects.filter(season=season_2)
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_4, score=5)
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_5, score=5)
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_6, score=15)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek_4, score=5)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek_5, score=15)
        ManagerPerformance.objects.create(manager=manager_2, gameweek=gameweek_6, score=15)
        ManagerPerformance.objects.create(manager=manager_3, gameweek=gameweek_4, score=5)
        ManagerPerformance.objects.create(manager=manager_3, gameweek=gameweek_5, score=25)
        ManagerPerformance.objects.create(manager=manager_3, gameweek=gameweek_6, score=20)

        self.assertEqual(len(classic_league.managers), 3)
        self.assertEqual(classic_league.managers[0].current_score, 35)
        self.assertEqual(classic_league.managers[1].current_score, 20)
        self.assertEqual(classic_league.managers[2].current_score, 10)
        self.assertTrue(classic_league.managers[0].paid_entry)
        self.assertTrue(classic_league.managers[1].paid_entry)
        self.assertTrue(classic_league.managers[2].paid_entry)

        self.assertEqual(len(classic_league_2.managers), 3)
        self.assertEqual(classic_league_2.managers[0].current_score, 50)
        self.assertEqual(classic_league_2.managers[1].current_score, 35)
        self.assertEqual(classic_league_2.managers[2].current_score, 25)
        self.assertFalse(classic_league_2.managers[0].paid_entry)
        self.assertFalse(classic_league_2.managers[1].paid_entry)
        self.assertFalse(classic_league_2.managers[2].paid_entry)


class HeadToHeadLeagueTestCase(TestCase):

    def setUp(self):
        User = get_user_model()
        self.entrant_1 = User.objects.create(username='entrant_1')
        self.entrant_2 = User.objects.create(username='entrant_2')
        self.entrant_3 = User.objects.create(username='entrant_3')
        self.season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        league = League.objects.create(name='Test League', entry_fee=10, season=self.season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_3, league=league, paid_entry=True)
        ])
        HeadToHeadLeague.objects.create(league=league, fpl_league_id=1)
        Manager.objects.bulk_create([
            Manager(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1, season=self.season),
            Manager(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2, season=self.season),
            Manager(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3, season=self.season)
        ])
        Gameweek.objects.bulk_create([
            Gameweek(number=1, start_date='2017-08-01', end_date='2017-08-02', season=self.season),
            Gameweek(number=2, start_date='2017-08-08', end_date='2017-08-09', season=self.season),
            Gameweek(number=3, start_date='2017-08-15', end_date='2017-08-16', season=self.season)
        ])

    @patch('fpl.models.HeadToHeadMatch.calculate_score')
    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.datetime')
    @patch('fpl.models.FPLLeague.get_authorized_session')
    def test_retrieve_league_data(self, mock_get_authorized_session, mock_datetime, *_):
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
        mock_datetime.date.today.return_value = datetime.date(2018, 5, 10)
        mock_datetime.timedelta.side_effect = lambda *args, **kw: datetime.timedelta(*args, **kw)

        h2h_league = HeadToHeadLeague.objects.get()
        h2h_league.retrieve_league_data()


        self.assertEqual(Manager.objects.count(), 4)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Test Manager Team')
        self.assertEqual(League.objects.get().name, 'Test League 1')
        self.assertEqual(HeadToHeadMatch.objects.count(), 2)
        self.assertIsNotNone(h2h_league.last_updated)

    @patch('fpl.models.HeadToHeadMatch.calculate_score')
    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.datetime')
    @patch('fpl.models.FPLLeague.get_authorized_session')
    def test_retrieve_league_data_odd_number_of_entrants(self, mock_get_authorized_session, mock_datetime, *_):
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
                }
            ],
            'matches': {
                'has_next': False,
                'results': [
                    {
                        'id': 3,
                        'event': 3,
                        'entry_1_entry': 1,
                        'entry_1_points': 10,
                        'entry_2_entry': 'AVERAGE',
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
        mock_datetime.date.today.return_value = datetime.date(2018, 5, 10)
        mock_datetime.timedelta.side_effect = lambda *args, **kw: datetime.timedelta(*args, **kw)

        h2h_league = HeadToHeadLeague.objects.get()
        h2h_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 4)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1, season=self.season).team_name, 'Test Manager Team')
        self.assertEqual(League.objects.get().name, 'Test League 1')
        self.assertEqual(HeadToHeadMatch.objects.count(), 2)
        self.assertIsNotNone(h2h_league.last_updated)
        average_manager = Manager.objects.get(season=self.season, fpl_manager_id=h2h_league.fpl_league_id*-1)
        self.assertEqual(average_manager.team_name, 'AVERAGE')

    @patch('fpl.models.HeadToHeadMatch.calculate_score')
    @patch('fpl.models.Manager.retrieve_performance_data')
    @patch('fpl.models.FPLLeague.get_authorized_session')
    def test_retrieve_league_data_after_season_end_does_not_update(self, mock_get_authorized_session, *_):
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
        today = datetime.date.today()
        season = Season.objects.create(start_date='2018-08-01', end_date=today - datetime.timedelta(days=14))
        h2h_league.league.season = season
        h2h_league.league.save()
        h2h_league.retrieve_league_data()

        self.assertEqual(Manager.objects.count(), 3)
        self.assertEqual(Manager.objects.get(fpl_manager_id=1).team_name, 'Team 1')
        self.assertEqual(League.objects.get().name, 'Test League')
        self.assertEqual(HeadToHeadMatch.objects.count(), 0)
        self.assertIsNone(h2h_league.last_updated)
        mock_get_authorized_session.assert_not_called()

    @patch('fpl.models.Gameweek.retrieve_gameweek_data')
    @patch('fpl.models.HeadToHeadLeague.retrieve_league_data')
    def test_process_payouts(self, mock_retrieve_league_data, mock_retrieve_gameweek_data):
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

        mock_retrieve_gameweek_data.assert_called_once()
        mock_retrieve_league_data.assert_called_once()
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

    def test_managers(self):
        h2h_league = HeadToHeadLeague.objects.get()

        gameweek_1, gameweek_2, gameweek_3 = Gameweek.objects.order_by('start_date').all()
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

        self.assertEqual(len(h2h_league.managers), 3)
        self.assertEqual(h2h_league.managers[0].current_h2h_score, 35)
        self.assertEqual(h2h_league.managers[1].current_h2h_score, 20)
        self.assertEqual(h2h_league.managers[2].current_h2h_score, 10)
        self.assertTrue(h2h_league.managers[0].paid_entry)
        self.assertTrue(h2h_league.managers[1].paid_entry)
        self.assertTrue(h2h_league.managers[2].paid_entry)

        season_2 = Season.objects.create(start_date='2018-08-01', end_date='2019-05-13')
        league_2 = League.objects.create(name='Test League 2', entry_fee=10, season=season_2)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=league_2, paid_entry=False),
            LeagueEntrant(entrant=self.entrant_2, league=league_2, paid_entry=False),
            LeagueEntrant(entrant=self.entrant_3, league=league_2, paid_entry=False)
        ])
        h2h_league_2 = HeadToHeadLeague.objects.create(league=league_2, fpl_league_id=1)
        Manager.objects.bulk_create([
            Manager(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1, season=season_2),
            Manager(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2, season=season_2),
            Manager(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3, season=season_2)
        ])

        gameweek_4 = Gameweek.objects.create(number=1, start_date='2018-08-01', end_date='2018-08-02',
                                             season=h2h_league_2.league.season)
        gameweek_5 = Gameweek.objects.create(number=2, start_date='2018-08-08', end_date='2018-08-09',
                                             season=h2h_league_2.league.season)
        gameweek_6 = Gameweek.objects.create(number=3, start_date='2018-08-15', end_date='2018-08-16',
                                             season=h2h_league_2.league.season)

        manager_1, manager_2, manager_3 = Manager.objects.filter(season=season_2)

        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_1, gameweek=gameweek_4, score=5)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_1, gameweek=gameweek_5, score=5)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_1, gameweek=gameweek_6, score=15)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_2, gameweek=gameweek_4, score=5)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_2, gameweek=gameweek_5, score=15)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_2, gameweek=gameweek_6, score=15)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_3, gameweek=gameweek_4, score=5)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_3, gameweek=gameweek_5, score=25)
        HeadToHeadPerformance.objects.create(h2h_league=h2h_league_2, manager=manager_3, gameweek=gameweek_6, score=20)

        self.assertEqual(len(h2h_league_2.managers), 3)
        self.assertEqual(h2h_league_2.managers[0].current_h2h_score, 50)
        self.assertEqual(h2h_league_2.managers[1].current_h2h_score, 35)
        self.assertEqual(h2h_league_2.managers[2].current_h2h_score, 25)
        self.assertFalse(h2h_league_2.managers[0].paid_entry)
        self.assertFalse(h2h_league_2.managers[1].paid_entry)
        self.assertFalse(h2h_league_2.managers[2].paid_entry)


class HeadToHeadMatchTestCase(TestCase):
    def test_calculate_score(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1')
        entrant_2 = User.objects.create(username='entrant_2')
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True)
        ])
        h2h_league = HeadToHeadLeague.objects.create(league=league, fpl_league_id=1)
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1, season=season)
        manager_2 = Manager.objects.create(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2, season=season)
        gameweek = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03', season=season)
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
        self.season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        self.season.refresh_from_db()
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1, season=self.season)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03',
                                             season=self.season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11',
                                             season=self.season)
        ManagerPerformance.objects.create(manager=manager_1, gameweek=gameweek_1, score=0)

    @patch('fpl.models.datetime')
    @patch('fpl.models.requests.get')
    def test_retrieve_performance_data(self, mock_requests_get, mock_datetime):
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
        mock_datetime.date.today.return_value = datetime.date(2018, 5, 10)
        mock_datetime.timedelta.side_effect = lambda *args, **kw: datetime.timedelta(*args, **kw)

        manager = Manager.objects.get()
        manager.retrieve_performance_data(self.season)

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

    @patch('fpl.models.requests.get')
    def test_retrieve_league_performance_after_season_end_does_not_update(self, mock_requests_get):
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
        today = datetime.date.today()
        season = Season.objects.create(start_date='2018-08-01', end_date=today - datetime.timedelta(days=14))
        manager.retrieve_performance_data(season)

        self.assertEqual(ManagerPerformance.objects.count(), 1)
        self.assertEqual(
            ManagerPerformance.objects.get(
                manager=manager,
                gameweek=Gameweek.objects.get(number=1)
            ).score,
            0
        )
        mock_requests_get.assert_not_called()


class GameweekTestCase(TestCase):

    @patch('fpl.models.datetime')
    @patch('fpl.models.requests.get')
    def test_retrieve_gameweek_data(self, mock_requests_get, mock_datetime):
        fixture_data = [
            {
                "kickoff_time": "2017-08-11T18:45:00Z",
                "event": 1
            }, {

                "kickoff_time": "2017-08-12T11:30:00Z",
                "event": 2
            },
            {

                "kickoff_time": None,
                "event": None
            },
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
        mock_datetime.date.today.return_value = datetime.date(2018, 5, 10)
        mock_datetime.timedelta.side_effect = lambda *args, **kw: datetime.timedelta(*args, **kw)

        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        season.refresh_from_db()
        Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03', season=season)

        Gameweek.retrieve_gameweek_data(season)

        self.assertEqual(Gameweek.objects.count(), 2)
        self.assertEqual(Gameweek.objects.get(number=1).start_date, datetime.date(2017, 8, 11))
        self.assertEqual(Gameweek.objects.get(number=2).start_date, datetime.date(2017, 8, 18))

    @patch('fpl.models.requests.get')
    @patch('fpl.models.timezone.now', side_effect=lambda: datetime.datetime.now())
    def test_retrieve_gameweek_data_does_nothing_after_season_end(self, mock_timezone_now, mock_requests_get):
        season = Season.objects.create(start_date='2017-08-01', end_date=timezone.now() - datetime.timedelta(days=13))
        season.refresh_from_db()

        Gameweek.retrieve_gameweek_data(season)

        self.assertEqual(mock_requests_get.call_count, 2)

        mock_requests_get.reset_mock()

        season = Season.objects.create(start_date='2017-08-01', end_date=timezone.now() - datetime.timedelta(days=14))
        season.refresh_from_db()

        Gameweek.retrieve_gameweek_data(season)
        mock_requests_get.assert_not_called()


class ClassicPayoutTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.entrant_1 = User.objects.create(username='entrant_1')
        self.entrant_2 = User.objects.create(username='entrant_2')
        self.entrant_3 = User.objects.create(username='entrant_3')
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        self.league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=self.league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_2, league=self.league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_3, league=self.league, paid_entry=True)
        ])
        self.manager_1 = Manager.objects.create(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1, season=season)
        self.manager_2 = Manager.objects.create(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2, season=season)
        self.manager_3 = Manager.objects.create(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3, season=season)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03', season=season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11', season=season)
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
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18',
                                             season=self.league.season)
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

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18',
                                             season=self.league.season)
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

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18',
                                             season=self.league.season)
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
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        self.league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=self.entrant_1, league=self.league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_2, league=self.league, paid_entry=True),
            LeagueEntrant(entrant=self.entrant_3, league=self.league, paid_entry=True)
        ])
        self.manager_1 = Manager.objects.create(entrant=self.entrant_1, team_name='Team 1', fpl_manager_id=1, season=season)
        self.manager_2 = Manager.objects.create(entrant=self.entrant_2, team_name='Team 2', fpl_manager_id=2, season=season)
        self.manager_3 = Manager.objects.create(entrant=self.entrant_3, team_name='Team 3', fpl_manager_id=3, season=season)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03', season=season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11', season=season)
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
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18',
                                             season=self.league.season)
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

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18',
                                             season=self.league.season)
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

        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-18',
                                             season=self.league.season)
        HeadToHeadPerformance.objects.bulk_create([
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_1, gameweek=gameweek_3, score=2),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_2, gameweek=gameweek_3, score=0),
            HeadToHeadPerformance(h2h_league=self.h2h_league, manager=self.manager_3, gameweek=gameweek_3, score=0)
        ])

        with self.assertRaises(NotImplementedError):
            payout_1.calculate_winner()

        with self.assertRaises(NotImplementedError):
            payout_2.calculate_winner()

class ClassicLeagueRefreshViewTestCase(TestCase):

    @patch('fpl.models.ClassicLeague.process_payouts')
    def test_get_redirect_url(self, mock_process_payouts):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league_1 = League.objects.create(name='Test League 1', entry_fee=10, season=season)
        classic_league = ClassicLeague.objects.create(league=league_1, fpl_league_id=1)
        response = self.client.post(reverse('fpl:season:classic:process-payouts', args=[season.pk, classic_league.pk]))
        mock_process_payouts.assert_called_once()

        mock_process_payouts.reset_mock()

        classic_league.last_updated = timezone.now()
        classic_league.save()
        response = self.client.post(reverse('fpl:season:classic:process-payouts', args=[season.pk, classic_league.pk]))
        mock_process_payouts.assert_not_called()


class ClassicLeagueListViewTestCase(TestCase):
    def test_title(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        response = self.client.get(reverse('fpl:season:classic:list', args=[season.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Classic Leagues')
        self.assertQuerysetEqual(response.context['league_list'], [])

    def test_classic_leagues_displayed(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league_1 = League.objects.create(name='Test League 1', entry_fee=10, season=season)
        ClassicLeague.objects.create(league=league_1, fpl_league_id=1)

        league_2 = League.objects.create(name='Test League 2', entry_fee=10, season=season)
        ClassicLeague.objects.create(league=league_2, fpl_league_id=2)

        response = self.client.get(reverse('fpl:season:classic:list', args=[season.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test League 1')
        self.assertContains(response, 'Test League 2')
        self.assertQuerysetEqual(response.context['league_list'].order_by('league'),
                                 ['<ClassicLeague: (2017-08-01 - 2018-05-15) - Test League 1>', '<ClassicLeague: (2017-08-01 - 2018-05-15) - Test League 2>'])


class ClassicLeagueDetailViewTestCase(TestCase):
    def test_league_exists(self):
        response = self.client.get(reverse('fpl:season:classic:detail', args=[1, 1]))
        self.assertEqual(response.status_code, 404)

    def test_title(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league_1 = League.objects.create(name='Test League 1', entry_fee=10, season=season)
        classic_league = ClassicLeague.objects.create(league=league_1, fpl_league_id=1)
        response = self.client.get(reverse('fpl:season:classic:detail', args=[season.pk, classic_league.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Classic League: Test League 1')

    def test_entrants(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1', first_name='Test', last_name='User 1')
        entrant_2 = User.objects.create(username='entrant_2', first_name='Test', last_name='User 2')
        entrant_3 = User.objects.create(username='entrant_3', first_name='Test', last_name='User 3')
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=False),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        classic_league = ClassicLeague.objects.create(league=league, fpl_league_id=1)
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1, season=season)
        manager_2 = Manager.objects.create(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2, season=season)
        manager_3 = Manager.objects.create(entrant=entrant_3, team_name='Team 3', fpl_manager_id=3, season=season)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03', season=season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11', season=season)
        ManagerPerformance.objects.bulk_create([
            ManagerPerformance(manager=manager_1, gameweek=gameweek_1, score=0),
            ManagerPerformance(manager=manager_2, gameweek=gameweek_1, score=10),
            ManagerPerformance(manager=manager_3, gameweek=gameweek_1, score=0),
            ManagerPerformance(manager=manager_1, gameweek=gameweek_2, score=0),
            ManagerPerformance(manager=manager_2, gameweek=gameweek_2, score=10),
            ManagerPerformance(manager=manager_3, gameweek=gameweek_2, score=30)
        ])

        response = self.client.get(reverse('fpl:season:classic:detail', args=[season.pk, classic_league.pk]))
        self.assertQuerysetEqual(response.context['object'].managers.order_by('team_name'),
                                 ['<Manager: Team 1 - entrant_1>', '<Manager: Team 2 - entrant_2>',
                                  '<Manager: Team 3 - entrant_3>'])
        self.assertContains(response, 'Team')
        self.assertContains(response, 'Manager')
        self.assertContains(response, 'Entry Paid')
        self.assertContains(response, 'Score')
        self.assertNotContains(response, 'Head To Head Score')

        self.assertContains(response, 'Team 1')
        self.assertContains(response, 'Test User 1')
        self.assertContains(response, 'False')
        self.assertContains(response, 0)
        self.assertContains(response, 'Team 2')
        self.assertContains(response, 'Test User 2')
        self.assertContains(response, 'True')
        self.assertContains(response, 20)
        self.assertContains(response, 'Team 3')
        self.assertContains(response, 'Test User 3')
        self.assertContains(response, 30)

    def test_payouts(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1', first_name='Test', last_name='User 1')
        entrant_2 = User.objects.create(username='entrant_2', first_name='Test', last_name='User 2')
        entrant_3 = User.objects.create(username='entrant_3', first_name='Test', last_name='User 3')
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=False),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        classic_league = ClassicLeague.objects.create(league=league, fpl_league_id=1)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-02', season=season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-09', season=season)
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-16', season=season)
        payout_1 = ClassicPayout.objects.create(
            league=classic_league.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date=gameweek_1.start_date,
            end_date=gameweek_1.end_date,
            winner=entrant_1,
            paid_out=True
        )
        payout_2 = ClassicPayout.objects.create(
            league=classic_league.league,
            name='Test Payout 2',
            amount=20,
            position=2,
            start_date=gameweek_2.start_date,
            end_date=gameweek_2.end_date,
            winner=entrant_2,
            paid_out=False
        )
        response = self.client.get(reverse('fpl:season:classic:detail', args=[season.pk, classic_league.pk]))
        self.assertQuerysetEqual(response.context['object'].league.payout_set.all().order_by('start_date'),
                                 ['<Payout: (2017-08-01 - 2018-05-15) - Test League - Test Payout 1 Position 1 (2017-08-01-2017-08-02): 10.00>',
                                  '<Payout: (2017-08-01 - 2018-05-15) - Test League - Test Payout 2 Position 2 (2017-08-08-2017-08-09): 20.00>'])

        self.assertContains(response, 'Name')
        self.assertContains(response, 'Position')
        self.assertContains(response, 'Start Date')
        self.assertContains(response, 'End Date')
        self.assertContains(response, 'Amount')
        self.assertContains(response, 'Winner')
        self.assertContains(response, 'Paid Out')

        self.assertContains(response, 'Test Payout 1')
        self.assertContains(response, '1')
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_1.start_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_1.end_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response, '10.00')
        self.assertContains(response, 'Test User 1')
        self.assertContains(response, 'True')

        self.assertContains(response, 'Test Payout 2')
        self.assertContains(response, '1')
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_2.start_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_2.end_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response, '20.00')
        self.assertContains(response, 'Test User 2')
        self.assertContains(response, 'False')

    def test_last_updated(self):
        now = timezone.now()
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        classic_league = ClassicLeague.objects.create(league=league, fpl_league_id=1, last_updated=now)
        response = self.client.get(reverse('fpl:season:classic:detail', args=[season.pk, classic_league.pk]))

        self.assertContains(response, 'Last Updated')
        ampm = ''.join([i.lower() + '.' for i in now.strftime('%p')])
        self.assertContains(response, now.strftime('%b. %-d, %Y, %-I:%M ' + ampm))


class HeadToHeadLeagueRefreshViewTestCase(TestCase):

    @patch('fpl.models.HeadToHeadLeague.process_payouts')
    def test_get_redirect_url(self, mock_process_payouts):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league_1 = League.objects.create(name='Test League 1', entry_fee=10, season=season)
        head_to_head_league = HeadToHeadLeague.objects.create(league=league_1, fpl_league_id=1)
        response = self.client.post(reverse('fpl:season:head-to-head:process-payouts', args=[season.pk, head_to_head_league.pk]))
        mock_process_payouts.assert_called_once()
        mock_process_payouts.reset_mock()

        head_to_head_league.last_updated = timezone.now()
        head_to_head_league.save()
        response = self.client.post(reverse('fpl:season:head-to-head:process-payouts', args=[season.pk, head_to_head_league.pk]))
        mock_process_payouts.assert_not_called()


class HeadToHeadLeagueListViewTestCase(TestCase):
    def test_title(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        response = self.client.get(reverse('fpl:season:head-to-head:list', args=[season.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Head To Head Leagues')
        self.assertQuerysetEqual(response.context['league_list'], [])

    def test_head_to_head_leagues_displayed(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-15')
        league_1 = League.objects.create(name='Test League 1', entry_fee=10, season=season)
        HeadToHeadLeague.objects.create(league=league_1, fpl_league_id=1)

        league_2 = League.objects.create(name='Test League 2', entry_fee=10, season=season)
        HeadToHeadLeague.objects.create(league=league_2, fpl_league_id=2)

        response = self.client.get(reverse('fpl:season:head-to-head:list', args=[season.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test League 1')
        self.assertContains(response, 'Test League 2')
        self.assertQuerysetEqual(response.context['league_list'].order_by('league'),
                                 ['<HeadToHeadLeague: (2017-08-01 - 2018-05-15) - Test League 1>', '<HeadToHeadLeague: (2017-08-01 - 2018-05-15) - Test League 2>'])


class HeadToHeadLeagueDetailViewTestCase(TestCase):
    def test_league_exists(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        response = self.client.get(reverse('fpl:season:head-to-head:detail', args=[season.pk, 1]))
        self.assertEqual(response.status_code, 404)

    def test_title(self):
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        league_1 = League.objects.create(name='Test League 1', entry_fee=10, season=season)
        head_to_head_league = HeadToHeadLeague.objects.create(league=league_1, fpl_league_id=1)
        response = self.client.get(reverse('fpl:season:head-to-head:detail', args=[season.pk, head_to_head_league.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Head To Head League: Test League 1')

    def test_entrants(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1', first_name='Test', last_name='User 1')
        entrant_2 = User.objects.create(username='entrant_2', first_name='Test', last_name='User 2')
        entrant_3 = User.objects.create(username='entrant_3', first_name='Test', last_name='User 3')
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=False),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        head_to_head_league = HeadToHeadLeague.objects.create(league=league, fpl_league_id=1)
        manager_1 = Manager.objects.create(entrant=entrant_1, team_name='Team 1', fpl_manager_id=1, season=season)
        manager_2 = Manager.objects.create(entrant=entrant_2, team_name='Team 2', fpl_manager_id=2, season=season)
        manager_3 = Manager.objects.create(entrant=entrant_3, team_name='Team 3', fpl_manager_id=3, season=season)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-03', season=season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-11', season=season)

        HeadToHeadPerformance.objects.bulk_create([
            HeadToHeadPerformance(h2h_league=head_to_head_league, manager=manager_1, gameweek=gameweek_1, score=0),
            HeadToHeadPerformance(h2h_league=head_to_head_league, manager=manager_2, gameweek=gameweek_1, score=1),
            HeadToHeadPerformance(h2h_league=head_to_head_league, manager=manager_3, gameweek=gameweek_1, score=0),
            HeadToHeadPerformance(h2h_league=head_to_head_league, manager=manager_1, gameweek=gameweek_2, score=0),
            HeadToHeadPerformance(h2h_league=head_to_head_league, manager=manager_2, gameweek=gameweek_2, score=1),
            HeadToHeadPerformance(h2h_league=head_to_head_league, manager=manager_3, gameweek=gameweek_2, score=3)
        ])

        response = self.client.get(reverse('fpl:season:head-to-head:detail', args=[season.pk, head_to_head_league.pk]))
        self.assertQuerysetEqual(sorted(response.context['object'].managers, key=lambda x: x.team_name),
                                 ['<Manager: Team 1 - entrant_1>', '<Manager: Team 2 - entrant_2>',
                                  '<Manager: Team 3 - entrant_3>'])
        self.assertContains(response, 'Team')
        self.assertContains(response, 'Manager')
        self.assertContains(response, 'Entry Paid')
        self.assertContains(response, 'Score')
        self.assertContains(response, 'Head To Head Score')

        self.assertContains(response, 'Team 1')
        self.assertContains(response, 'Test User 1')
        self.assertContains(response, 'False')
        self.assertContains(response, 0)
        self.assertContains(response, 'Team 2')
        self.assertContains(response, 'Test User 2')
        self.assertContains(response, 'True')
        self.assertContains(response, 2)
        self.assertContains(response, 'Team 3')
        self.assertContains(response, 'Test User 3')
        self.assertContains(response, 3)

    def test_payouts(self):
        User = get_user_model()
        entrant_1 = User.objects.create(username='entrant_1', first_name='Test', last_name='User 1')
        entrant_2 = User.objects.create(username='entrant_2', first_name='Test', last_name='User 2')
        entrant_3 = User.objects.create(username='entrant_3', first_name='Test', last_name='User 3')
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        LeagueEntrant.objects.bulk_create([
            LeagueEntrant(entrant=entrant_1, league=league, paid_entry=False),
            LeagueEntrant(entrant=entrant_2, league=league, paid_entry=True),
            LeagueEntrant(entrant=entrant_3, league=league, paid_entry=True)
        ])
        head_to_head_league = HeadToHeadLeague.objects.create(league=league, fpl_league_id=1)
        gameweek_1 = Gameweek.objects.create(number=1, start_date='2017-08-01', end_date='2017-08-02', season=season)
        gameweek_2 = Gameweek.objects.create(number=2, start_date='2017-08-08', end_date='2017-08-09', season=season)
        gameweek_3 = Gameweek.objects.create(number=3, start_date='2017-08-15', end_date='2017-08-16', season=season)
        payout_1 = HeadToHeadPayout.objects.create(
            league=head_to_head_league.league,
            name='Test Payout 1',
            amount=10,
            position=1,
            start_date=gameweek_1.start_date,
            end_date=gameweek_1.end_date,
            winner=entrant_1,
            paid_out=True
        )
        payout_2 = HeadToHeadPayout.objects.create(
            league=head_to_head_league.league,
            name='Test Payout 2',
            amount=20,
            position=2,
            start_date=gameweek_2.start_date,
            end_date=gameweek_2.end_date,
            winner=entrant_2,
            paid_out=False
        )
        response = self.client.get(reverse('fpl:season:head-to-head:detail', args=[season.pk, head_to_head_league.pk]))
        self.assertQuerysetEqual(response.context['object'].league.payout_set.all().order_by('start_date'),
                                 ['<Payout: (2017-08-01 - 2018-05-13) - Test League - Test Payout 1 Position 1 (2017-08-01-2017-08-02): 10.00>',
                                  '<Payout: (2017-08-01 - 2018-05-13) - Test League - Test Payout 2 Position 2 (2017-08-08-2017-08-09): 20.00>'])

        self.assertContains(response, 'Name')
        self.assertContains(response, 'Position')
        self.assertContains(response, 'Start Date')
        self.assertContains(response, 'End Date')
        self.assertContains(response, 'Amount')
        self.assertContains(response, 'Winner')
        self.assertContains(response, 'Paid Out')

        self.assertContains(response, 'Test Payout 1')
        self.assertContains(response, '1')
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_1.start_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_1.end_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response, '10.00')
        self.assertContains(response, 'Test User 1')
        self.assertContains(response, 'True')

        self.assertContains(response, 'Test Payout 2')
        self.assertContains(response, '1')
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_2.start_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response,
                            datetime.datetime.strptime(gameweek_2.end_date, '%Y-%m-%d').strftime('%b. %-d, %Y'))
        self.assertContains(response, '20.00')
        self.assertContains(response, 'Test User 2')
        self.assertContains(response, 'False')

    def test_last_updated(self):
        now = timezone.now()
        season = Season.objects.create(start_date='2017-08-01', end_date='2018-05-13')
        league = League.objects.create(name='Test League', entry_fee=10, season=season)
        head_to_head_league = HeadToHeadLeague.objects.create(league=league, fpl_league_id=1, last_updated=now)
        response = self.client.get(reverse('fpl:season:head-to-head:detail', args=[season.pk, head_to_head_league.pk]))

        self.assertContains(response, 'Last Updated')
        ampm = ''.join([i.lower() + '.' for i in now.strftime('%p')])
        self.assertContains(response, now.strftime('%b. %-d, %Y, %-I:%M ' + ampm))
