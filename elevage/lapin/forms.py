from django import forms
from .models import Elevage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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
    
    def clean_argent(self):
        argent = self.cleaned_data.get('argent')
        if argent is not None and argent < 0:
            raise forms.ValidationError("Le montant de départ ne peut pas être négatif.")
        return argent
        
class Actions(forms.Form):
    lapins_males_vendus = forms.IntegerField(min_value=0, required=False, label="Lapins mâles vendus", initial=0)
    lapins_femelles_vendus = forms.IntegerField(min_value=0, required=False, label="Lapins femelles vendues", initial=0)
    nourriture_achetee = forms.IntegerField(min_value=0, required=False, label="Quantité de nourriture achetée (g)", initial=0)
    cages_achetees = forms.IntegerField(min_value=0, required=False, label="Nombre de cages achetées", initial=0)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Requis. Entrez une adresse valide.")
    first_name = forms.CharField(max_length=30, required=True, label="Prénom")
    last_name = forms.CharField(max_length=30, required=True, label="Nom")

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
class RessourcesBonusForm(forms.Form):
    RESSOURCES_CHOICES = [
        ('nourriture', '🍽 +20 000g de nourriture'),
        ('cages', '🏠 +1 cage'),
        ('argent', '💰 +500 €'),
    ]
    type_bonus = forms.ChoiceField(
        choices=RESSOURCES_CHOICES,
        widget=forms.RadioSelect,
        label="Choisissez un bonus (1 par tour)",
        required=False  # Permet de ne rien choisir
    )

