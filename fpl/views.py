# Create your views here.
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, RedirectView

from fpl.models import ClassicLeague


class ClassicLeagueListView(ListView):
    model = ClassicLeague
    context_object_name = 'classic_league_list'


class ClassicLeagueDetailView(DetailView):
    model = ClassicLeague
    context_object_name = 'classic_league'


class ClassicLeagueRefreshView(RedirectView):
    permanent = False
    http_method_names = ['post']

    def get_redirect_url(self, *args, **kwargs):
        classic_league_id = kwargs['pk']
        classic_league = get_object_or_404(ClassicLeague, pk=classic_league_id)
        if timezone.timedelta(hours=1) < timezone.now() - classic_league.last_updated:
            classic_league.process_payouts()
        return reverse('fpl:classic-league:detail', args=[classic_league_id])
