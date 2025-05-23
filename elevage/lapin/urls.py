from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu, name='menu'),  # Page d'accueil
    path('elevages/nouveau/', views.nouveau, name='nouveau_elevage'),
    path('elevages/', views.liste, name='liste_elevages'),
    path('elevages/<int:elevage_id>/', views.elevage, name='detail_elevage'),
    path('elevages/regles/', views.regles_jeu, name='regles_jeu'),
    path('elevages/<int:elevage_id>/gestion_lapins/', views.gestion_lapins, name='gestion_lapins'),
    path('signup/', views.signup_view, name='signup'),
    path('premium/', views.premium_info, name='premium_info'),

]
