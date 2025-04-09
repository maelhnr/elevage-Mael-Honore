from django.shortcuts import render, redirect, get_object_or_404
from .forms import ElevageForm, Actions
from .models import Elevage, Individu

def nouveau(request):
    if request.method == 'POST':
        form = ElevageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_elevages')  # Redirection à définir plus tard
    else:
        form = ElevageForm()
    return render(request, 'elevage/nouveau.html', {'form': form})

def liste(request):
    elevages = Elevage.objects.all().order_by('-date_creation')
    return render(request, 'elevage/liste.html', {'elevages': elevages})

def elevage(request, elevage_id):
    elevage = get_object_or_404(Elevage, id=elevage_id)
    individus = Individu.objects.filter(elevage=elevage, etat='PRESENT')
    form = Actions(request.POST or None)

    if request.method == "POST" and form.is_valid():
        # Extraction des données
        vendus_m = form.cleaned_data['lapins_males_vendus']
        vendus_f = form.cleaned_data['lapins_femelles_vendus']
        nourriture_achetee = form.cleaned_data['nourriture_achetee']
        cages_achetees = form.cleaned_data['cages_achetees']

        # Comptage des lapins actuels
        nb_males = individus.filter(sexe='M').count()
        nb_femelles = individus.filter(sexe='F').count()

        # Vérification des ordres
        prix_nourriture = 0.002
        prix_cage = 10
        cout_total = nourriture_achetee * prix_nourriture + cages_achetees * prix_cage  # Exemple : 2€/kg de nourriture, 10€/cage
        if vendus_m > nb_males or vendus_f > nb_femelles:
            form.add_error(None, "Vous ne pouvez pas vendre plus de lapins que vous n'en avez.")
        elif cout_total > elevage.argent:
            form.add_error(None, "Fonds insuffisants pour cet achat.")
        else:
            # Marquer les lapins comme vendus
            individus.filter(sexe='M')[:vendus_m].update(etat='VENDU')
            individus.filter(sexe='F')[:vendus_f].update(etat='VENDU')

            # Appliquer les achats
            elevage.quantite_nourriture += nourriture_achetee
            elevage.nombre_cages += cages_achetees
            elevage.argent -= cout_total

            elevage.save()
            return redirect('elevage_detail', elevage_id=elevage.id)

    context = {
        'elevage': elevage,
        'individus': individus,
        'form': form,
    }
    return render(request, 'elevage/elevage.html', context)