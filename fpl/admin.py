from django.contrib import admin

from .models import Manager, ClassicLeague, HeadToHeadLeague

admin.site.register(Manager)
admin.site.register(ClassicLeague)
admin.site.register(HeadToHeadLeague)
