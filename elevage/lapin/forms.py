from django import forms
from .models import Elevage

class ElevageForm(forms.ModelForm):
    class Meta:
        model = Elevage
        fields = ['nom_joueur', 'nombre_males', 'nombre_femelles', 'quantite_nourriture', 'nombre_cages', 'argent']
        labels = {
            'nom_joueur': 'Nom du joueur',
            'nombre_males': 'Nombre de mâles',
            'nombre_femelles': 'Nombre de femelles',
            'quantite_nourriture': 'Quantité de nourriture (g)',
            'nombre_cages': 'Nombre de cages',
            'argent': 'Argent (€)',
        }
        
class Actions(forms.Form):
    lapins_males_vendus = forms.IntegerField(min_value=0, required=False, label="Lapins mâles vendus", initial=0)
    lapins_femelles_vendus = forms.IntegerField(min_value=0, required=False, label="Lapins femelles vendues", initial=0)
    nourriture_achetee = forms.IntegerField(min_value=0, required=False, label="Quantité de nourriture achetée (g)", initial=0)
    cages_achetees = forms.IntegerField(min_value=0, required=False, label="Nombre de cages achetées", initial=0)
