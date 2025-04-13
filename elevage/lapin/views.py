from django.shortcuts import render, redirect, get_object_or_404
from .forms import ElevageForm, Actions
from .models import Elevage, Individu, Regle

def nouveau(request):
    if request.method == 'POST':
        form = ElevageForm(request.POST)
        if form.is_valid():
            elevage = form.save()

            # Création automatique des individus
            nb_femelles = form.cleaned_data['nombre_femelles']
            nb_males = form.cleaned_data['nombre_males']    

            for _ in range(nb_femelles):
                Individu.objects.create(
                    elevage=elevage,
                    sexe='F',
                    age=0,
                    etat='P'  # Présent
                )
            for _ in range(nb_males):
                Individu.objects.create(
                    elevage=elevage,
                    sexe='M',
                    age=0,
                    etat='P'  # Présent
                )

            return redirect('detail_elevage', elevage_id=elevage.id)
    else:
        form = ElevageForm()

    return render(request, 'elevage/nouveau.html', {'form': form})


def liste(request):
    query = request.GET.get('q', '')
    if query:
        elevages = Elevage.objects.filter(nom_joueur__icontains=query)
    else:
        elevages = Elevage.objects.all()

    context = {
        'elevages': elevages,
        'query': query,
    }
    return render(request, 'elevage/liste.html', context)


def elevage(request, elevage_id):
    elevage = get_object_or_404(Elevage, id=elevage_id)
    individus = Individu.objects.filter(
    elevage=elevage,
    etat__in=['P', 'G'] 
    )
    form = Actions(request.POST or None)
    resultats_tour = None
    form_is_valid = request.method == "POST" and form.is_valid()
    
    if elevage.fin_du_jeu:
        form = None

    elif form_is_valid:
        # Extraction des données
        vendus_m = form.cleaned_data['lapins_males_vendus'] or 0
        vendus_f = form.cleaned_data['lapins_femelles_vendus'] or 0
        nourriture_achetee = form.cleaned_data['nourriture_achetee'] or 0
        cages_achetees = form.cleaned_data['cages_achetees'] or 0

        # Comptage des lapins actuels
        nb_males = individus.filter(sexe='M').count()
        nb_femelles = individus.filter(sexe='F').count()

        # Vérification des ordres
        regle = Regle.objects.first()  # On suppose toujours qu’il n’y en a qu’une
        cout_total = nourriture_achetee * regle.prix_nourriture + cages_achetees * regle.prix_cage
        if vendus_m > nb_males or vendus_f > nb_femelles:
            form.add_error(None, "Vous ne pouvez pas vendre plus de lapins que vous n'en avez.")
        elif cout_total > elevage.argent:
            form.add_error(None, "Fonds insuffisants pour cet achat.")
        else:
            # Marquer les lapins comme vendus 
            lapins_males = individus.filter(sexe='M')[:vendus_m]
            for lapin in lapins_males:
                lapin.etat = 'VENDU'
                lapin.save()

            lapins_femelles = individus.filter(sexe='F')[:vendus_f]
            for lapin in lapins_femelles:
                lapin.etat = 'VENDU'
                lapin.save()

            # Appliquer les achats
            resultats_tour = elevage.jouer_tour(nourriture_achetee, cages_achetees)
            form = Actions()  # Reset form après un tour


    context = {
        'elevage': elevage,
        'individus': individus,
        'form': form if not elevage.fin_du_jeu else None,
        'resultats_tour': resultats_tour if form_is_valid else None,
        'fin_du_jeu': elevage.fin_du_jeu,
        'lapins_vendus_m': vendus_m if form_is_valid else 0,
        'lapins_vendus_f': vendus_f if form_is_valid else 0,
    }
    return render(request, 'elevage/elevage.html', context)


def menu(request):
    return render(request, 'menu.html', {'hide_navbar': True})

def regles_jeu(request):
    return render(request, 'elevage/regles.html')

