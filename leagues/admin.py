from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import League, LeagueEntrant, LeagueType

admin.site.register(League)
admin.site.register(LeagueType)
admin.site.register(LeagueEntrant)
