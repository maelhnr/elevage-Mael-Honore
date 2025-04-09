from django.contrib import admin
from .models import Elevage, Individu

@admin.register(Elevage)
class ElevageAdmin(admin.ModelAdmin):
    list_display = ('nom_joueur', 'nombre_males', 'nombre_femelles', 'quantite_nourriture', 'nombre_cages', 'argent', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('nom_joueur',)
    
@admin.register(Individu)
class IndividuAdmin(admin.ModelAdmin):
    list_display = ('elevage', 'sexe', 'age', 'etat')
    list_filter = ('elevage', 'sexe', 'etat')
