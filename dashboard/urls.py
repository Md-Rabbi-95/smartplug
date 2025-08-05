from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/power-data/', views.power_data_api, name='power_data_api'),
     path('api/energy-today/', views.energy_today_api, name='energy_today_api'),
    path('api/turn-on/', views.turn_on_view, name='turn_on'),
    path('api/turn-off/', views.turn_off_view, name='turn_off'),
    path('api/download-csv/', views.download_csv, name='download_csv'),  
]