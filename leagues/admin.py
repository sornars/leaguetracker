from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from leagues.models import Manager

from .models import League, LeagueType

admin.site.register(League)
admin.site.register(LeagueType)


class ManagerInline(admin.StackedInline):
    model = Manager
    can_delete = False
    verbose_name_plural = 'manager'
    min_num = 1
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (ManagerInline, )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
