from django.urls import path
from . import views

urlpatterns = [
    path('nouveau/', views.nouveau, name='nouveau_elevage'),
]
