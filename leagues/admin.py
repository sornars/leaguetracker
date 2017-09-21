from django.contrib import admin

from .models import League, LeagueEntrant, PositionPayout, PeriodPayout

admin.site.register(League)
admin.site.register(LeagueEntrant)
admin.site.register(PositionPayout)
admin.site.register(PeriodPayout)