# Create your views here.
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, RedirectView

from fpl.models import ClassicLeague, HeadToHeadLeague
from leagues.models import Season


class LeagueListView(ListView):

    def get_queryset(self):
        return self.model.objects.filter(league__season=self.kwargs['season_pk'])


class ClassicLeagueListView(LeagueListView):
    model = ClassicLeague
    context_object_name = 'league_list'
    template_name = 'fpl/league_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Classic Leagues'
        context['base_url'] = 'fpl:season:classic:detail'
        season = Season.objects.get(pk=self.kwargs['season_pk'])
        context['navbar_levels'] = [
            {
                'name': 'Seasons',
                'href': reverse('fpl:season:list')
            },
            {
                'name': str(season),
                'href': reverse('fpl:season:detail', args=[season.pk])
            },
            {
                'name': 'Classic Leagues',
                'href': reverse('fpl:season:classic:list', args=[season.pk])
            }
        ]
        return context


class HeadToHeadLeagueListView(LeagueListView):
    model = HeadToHeadLeague
    context_object_name = 'league_list'
    template_name = 'fpl/league_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Head To Head Leagues'
        context['base_url'] = 'fpl:season:head-to-head:detail'
        season = Season.objects.get(pk=self.kwargs['season_pk'])
        context['navbar_levels'] = [
            {
                'name': 'Seasons',
                'href': reverse('fpl:season:list')
            },
            {
                'name': str(season),
                'href': reverse('fpl:season:detail', args=[season.pk])
            },
            {
                'name': 'Head To Head Leagues',
                'href': reverse('fpl:season:head-to-head:list', args=[season.pk])
            }
        ]
        return context


class LeagueDetailView(DetailView):
    pk_url_kwarg = 'league_pk'


class ClassicLeagueDetailView(LeagueDetailView):
    model = ClassicLeague
    context_object_name = 'league'
    template_name = 'fpl/league_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Classic League'
        context['base_url'] = 'fpl:season:classic:process-payouts'
        season = Season.objects.get(pk=self.kwargs['season_pk'])
        league = self.model.objects.get(pk=self.kwargs['league_pk'])
        context['navbar_levels'] = [
            {
                'name': 'Seasons',
                'href': reverse('fpl:season:list')
            },
            {
                'name': str(season),
                'href': reverse('fpl:season:detail', args=[season.pk])
            },
            {
                'name': 'Classic Leagues',
                'href': reverse('fpl:season:classic:list', args=[season.pk])
            },
            {
                'name': league.league.name,
                'href': reverse('fpl:season:classic:detail', args=[season.pk, league.pk])
            }
        ]

        return context


class HeadToHeadLeagueDetailView(LeagueDetailView):
    model = HeadToHeadLeague
    context_object_name = 'league'
    template_name = 'fpl/league_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Head To Head League'
        context['base_url'] = 'fpl:season:head-to-head:process-payouts'
        season = Season.objects.get(pk=self.kwargs['season_pk'])
        league = self.model.objects.get(pk=self.kwargs['league_pk'])
        context['navbar_levels'] = [
            {
                'name': 'Seasons',
                'href': reverse('fpl:season:list')
            },
            {
                'name': str(season),
                'href': reverse('fpl:season:detail', args=[season.pk])
            },
            {
                'name': 'Head To Head Leagues',
                'href': reverse('fpl:season:head-to-head:list', args=[season.pk])
            },
            {
                'name': league.league.name,
                'href': reverse('fpl:season:head-to-head:detail', args=[season.pk, league.pk])
            }
        ]
        return context


class LeagueRefreshView(RedirectView):
    permanent = False
    http_method_names = ['post']
    league_type = None
    base_url = ''

    def get_redirect_url(self, *args, **kwargs):
        season_id = kwargs['season_pk']
        league_id = kwargs['league_pk']
        league = get_object_or_404(self.league_type, pk=league_id)
        last_updated = league.last_updated if league.last_updated else timezone.now() - timezone.timedelta(hours=2)
        if timezone.timedelta(hours=1) < timezone.now() - last_updated:
            league.process_payouts()
        return reverse(self.base_url, args=[season_id, league_id])


class ClassicLeagueRefreshView(LeagueRefreshView):
    league_type = ClassicLeague
    base_url = 'fpl:season:classic:detail'


class HeadToHeadLeagueRefreshView(LeagueRefreshView):
    league_type = HeadToHeadLeague
    base_url = 'fpl:season:head-to-head:detail'


class SeasonListView(ListView):
    model = Season
    context_object_name = 'season_list'
    template_name = 'fpl/season_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['base_url'] = 'fpl:season:detail'
        context['navbar_levels'] = [
            {
                'name': 'Seasons',
                'href': reverse('fpl:season:list')
            }
        ]
        return context


class SeasonDetailView(DetailView):
    model = Season
    context_object_name = 'season'
    template_name = 'fpl/season_detail.html'
    pk_url_kwarg = 'season_pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        season = kwargs['object']
        context['navbar_levels'] = [
            {
                'name': 'Seasons',
                'href': reverse('fpl:season:list')
            },
            {
                'name': str(season),
                'href': reverse('fpl:season:detail', args=[season.pk])
            }
        ]
        context['league_types'] = [
            {
                'name': 'Classic Leagues',
                'href': reverse('fpl:season:classic:list', args=[season.pk])
            },
            {
                'name': 'Head To Head Leagues',
                'href': reverse('fpl:season:head-to-head:list', args=[season.pk])
            },
        ]
        return context
