from django.contrib import admin

from .models import Manager, ClassicLeague, ManagerPerformance

admin.site.register(Manager)
admin.site.register(ClassicLeague)
admin.site.register(ManagerPerformance)
