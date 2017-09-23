from unittest.mock import patch, Mock

from django.test import TestCase

from django.contrib.auth import get_user_model
from leagues.models import League, LeagueEntrant
from fpl.models import ClassicLeague, Manager, Gameweek, ManagerPerformance


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
    pass