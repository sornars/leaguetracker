from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from fpl.models import ClassicLeague, Gameweek, Manager, ManagerPerformance
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
