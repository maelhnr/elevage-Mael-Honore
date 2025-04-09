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
