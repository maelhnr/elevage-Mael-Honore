from django.urls import path
from . import views

urlpatterns = [
    path('elevages/nouveau/', views.nouveau, name='nouveau_elevage'),
    path('elevages/', views.liste, name='liste_elevages'),
    path('elevages/<int:elevage_id>/', views.elevage, name='detail_elevage'),
]
