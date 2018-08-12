from django.urls import include, path

from fpl import views

app_name = 'fpl'

classic_league_patterns = ([
                               path('', views.ClassicLeagueListView.as_view(), name='list'),
                               path('<int:league_pk>/', views.ClassicLeagueDetailView.as_view(), name='detail'),
                               path('<int:league_pk>/process-payouts', views.ClassicLeagueRefreshView.as_view(),
                                    name='process-payouts')
                           ], 'classic')

head_to_head_league_patterns = ([
                                    path('', views.HeadToHeadLeagueListView.as_view(), name='list'),
                                    path('<int:league_pk>/', views.HeadToHeadLeagueDetailView.as_view(), name='detail'),
                                    path('<int:league_pk>/process-payouts', views.HeadToHeadLeagueRefreshView.as_view(),
                                         name='process-payouts')
                                ], 'head-to-head')

season_patterns = ([
                       path('', views.SeasonListView.as_view(), name='list'),
                       path('<int:season_pk>/', views.SeasonDetailView.as_view(), name='detail'),
                       path('<int:season_pk>/classic-leagues/', include(classic_league_patterns)),
                       path('<int:season_pk>/head-to-head-leagues/', include(head_to_head_league_patterns))
                   ], 'season')

urlpatterns = [
    path('seasons/', include(season_patterns))
]
