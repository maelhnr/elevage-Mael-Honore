from django.urls import path
from . import views

urlpatterns = [
    path('nouveau/', views.nouveau, name='nouveau_elevage'),
    path('liste/', views.liste, name='liste_elevages'),
    path('elevage/<int:elevage_id>/', views.elevage, name='detail_elevage'),
]
