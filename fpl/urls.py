from django.urls import include, path

from fpl import views

app_name = 'fpl'
classic_league_patterns = ([
                               path('', views.ClassicLeagueListView.as_view(), name='list'),
                               path('<int:pk>/', views.ClassicLeagueDetailView.as_view(), name='detail'),
                               path('<int:pk>/process-payouts', views.ClassicLeagueRefreshView.as_view(),
                                    name='process-payouts')
                           ], 'classic')

head_to_head_league_patterns = ([
                                    path('', views.HeadToHeadLeagueListView.as_view(), name='list'),
                                    path('<int:pk>/', views.HeadToHeadLeagueDetailView.as_view(), name='detail'),
                                    path('<int:pk>/process-payouts', views.HeadToHeadLeagueRefreshView.as_view(),
                                         name='process-payouts')
                                ], 'head-to-head')

urlpatterns = [
    path('classic-leagues/', include(classic_league_patterns)),
    path('head-to-head-leagues/', include(head_to_head_league_patterns))
]
