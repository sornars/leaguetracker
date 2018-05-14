# Create your views here.
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, RedirectView

from fpl.models import ClassicLeague, HeadToHeadLeague


class ClassicLeagueListView(ListView):
    model = ClassicLeague
    context_object_name = 'league_list'
    template_name = 'fpl/league_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Classic Leagues'
        context['base_url'] = 'fpl:classic:detail'
        return context

class HeadToHeadLeagueListView(ListView):
    model = HeadToHeadLeague
    context_object_name = 'league_list'
    template_name = 'fpl/league_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Head To Head Leagues'
        context['base_url'] = 'fpl:head-to-head:detail'
        return context


class ClassicLeagueDetailView(DetailView):
    model = ClassicLeague
    context_object_name = 'league'
    template_name = 'fpl/league_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Classic League'
        context['base_url'] = 'fpl:classic:process-payouts'
        return context


class HeadToHeadLeagueDetailView(DetailView):
    model = HeadToHeadLeague
    context_object_name = 'league'
    template_name = 'fpl/league_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['league_type'] = 'Head To Head League'
        context['base_url'] = 'fpl:head-to-head:process-payouts'
        return context

class LeagueRefreshView(RedirectView):
    permanent = False
    http_method_names = ['post']
    league_type = None
    base_url = ''

    def get_redirect_url(self, *args, **kwargs):
        league_id = kwargs['pk']
        league = get_object_or_404(self.league_type, pk=league_id)
        if timezone.timedelta(hours=1) < timezone.now() - league.last_updated:
            league.process_payouts()
        return reverse(self.base_url, args=[league_id])

class ClassicLeagueRefreshView(LeagueRefreshView):
    league_type = ClassicLeague
    base_url = 'fpl:classic:detail'

class HeadToHeadLeagueRefreshView(LeagueRefreshView):
    league_type = HeadToHeadLeague
    base_url = 'fpl:head-to-head:detail'
