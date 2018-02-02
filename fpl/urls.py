from django.urls import include, path

from fpl import views

app_name = 'fpl'
classic_league_patterns = ([
    path('', views.ClassicLeagueListView.as_view(), name='list'),
    path('<int:pk>/', views.ClassicLeagueDetailView.as_view(), name='detail')
], 'classic-league')

urlpatterns = [
    path('classic-leagues/', include(classic_league_patterns))
]