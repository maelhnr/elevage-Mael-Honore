from django.contrib import admin
from .models import Elevage

@admin.register(Elevage)
class ElevageAdmin(admin.ModelAdmin):
    list_display = ('nom_joueur', 'nombre_males', 'nombre_femelles', 'quantite_nourriture', 'nombre_cages', 'argent', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('nom_joueur',)
