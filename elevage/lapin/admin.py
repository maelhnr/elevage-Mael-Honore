from django.contrib import admin
from .models import Elevage, Individu, Regle, Client

@admin.register(Elevage)
class ElevageAdmin(admin.ModelAdmin):
    list_display = ('nom_joueur', 'nombre_males', 'nombre_femelles', 'quantite_nourriture', 'nombre_cages', 'argent', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('nom_joueur',)
    
@admin.register(Individu)
class IndividuAdmin(admin.ModelAdmin):
    list_display = ('elevage', 'sexe', 'age', 'etat')
    list_filter = ('elevage', 'sexe', 'etat')
    
@admin.register(Regle)
class RegleAdmin(admin.ModelAdmin):
    list_display = (
        'prix_nourriture',
        'prix_cage',
        'prix_vente_lapin',
        'conso_2_mois',
        'conso_3_mois_et_plus',
        'age_min_gravide',
        'age_max_gravide',
        'duree_gestation',
        'nb_max_par_portee',
        'nb_max_individus_par_cage',
        'seuil_surpopulation',
    )

    search_fields = ('prix_nourriture', 'prix_cage', 'prix_vente_lapin')
    
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_premium')
    search_fields = ('user__username',)
    

