# Create your views here.
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, RedirectView

from fpl.models import ClassicLeague
from leagues.models import LeagueEntrant


class ClassicLeagueListView(ListView):
    model = ClassicLeague


class ClassicLeagueDetailView(DetailView):
    model = ClassicLeague

    def get_object(self, queryset=None):
        classic_league = super().get_object(queryset=queryset)
        classic_league.entrants = classic_league.league.entrants.annotate(
            score=Sum('manager__managerperformance__score')
        ).order_by('-score')
        # TODO: Combine queries
        for entrant in classic_league.entrants:
            entrant.paid_entry = LeagueEntrant.objects.filter(
                league=classic_league.league,
                entrant=entrant
            ).get().paid_entry
        return classic_league

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context


class ClassicLeagueRefreshView(RedirectView):
    permanent = False
    http_method_names = ['post']

    def get_redirect_url(self, *args, **kwargs):
        classic_league_id = kwargs['pk']
        classic_league = get_object_or_404(ClassicLeague, pk=classic_league_id)
        if timezone.timedelta(hours=1) < timezone.now() - classic_league.last_updated:
            classic_league.retrieve_league_data()
        return reverse('fpl:classic-league:detail', args=[classic_league_id])
