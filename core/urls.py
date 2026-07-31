from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('incidents/', views.all_incidents, name='all_incidents'),
    path('map/', views.full_map, name='full_map'),
    path('reports/', views.reports_view, name='reports'),

    # API endpoints
    path('api/incidents/', views.get_incidents, name='get_incidents'),
    path('api/signals/ingest/', views.ingest_signal, name='ingest_signal'),
    path('api/signals/all/', views.get_all_signals, name='get_all_signals'),
    path('api/presets/load/', views.load_preset, name='load_preset'),
    path('api/presets/reset/', views.reset_db, name='reset_db'),
    path('api/config/update/', views.update_config, name='update_config'),
    path('api/incidents/<str:incident_id>/override/', views.incident_override, name='incident_override'),
    path('api/chatbot/query/', views.chatbot_query, name='chatbot_query'),
    path('api/nearby/aid/', views.nearby_aid_layer, name='nearby_aid_layer'),
    path('api/feeds/gdacs/', views.fetch_gdacs_feeds, name='fetch_gdacs_feeds'),
    path('api/feeds/gdacs/sync/', views.sync_gdacs_live_feed, name='sync_gdacs_live_feed'),
]
