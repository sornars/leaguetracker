from django.contrib import admin

from .models import League, LeagueEntrant, Payout, Season

admin.site.register(League)
admin.site.register(LeagueEntrant)
admin.site.register(Payout)
admin.site.register(Season)
