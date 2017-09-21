import requests
from django.conf import settings
from django.db import models


from leagues.models import League


BASE_URL = 'https://fantasy.premierleague.com/drf/'


class ClassicLeague(models.Model):
    league = models.OneToOneField(League, on_delete=models.CASCADE)
    fpl_league_id = models.IntegerField(unique=True)

    def retrieve_league_data(self):
        response = requests.get(BASE_URL + 'leagues-classic-standings/' + str(self.fpl_league_id))
        data = response.json()
        self.league.name = data['league']['name']
        for manager in data['standings']['results']:
            Manager.objects.update_or_create(
                fpl_manager_id=manager['entry'],
                defaults={
                    'team_name': manager['entry_name']
                }
            )

    def __str__(self):
        return self.league.name

class Manager(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    team_name = models.CharField(max_length=50)
    fpl_manager_id = models.IntegerField()

    def __str__(self):
        return '{team_name} - {user}'.format(team_name=self.team_name, user=self.user)
