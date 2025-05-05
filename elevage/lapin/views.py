import json
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ElevageForm, Actions
from .models import Elevage, Individu, Regle, Tour
from django.core import serializers


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
        elevages = Elevage.objects.order_by('-date_creation')

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
    
    data_exists = False
    empty_data = {
                "labels": [],
                "nb_femelles_adultes": [],
                "nb_males_adultes": [],
                "nb_lapereaux": []
        }
    
    numero = elevage.tour
    ## graphe initial 
    
    
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
        regle, created = Regle.objects.get_or_create(defaults={
            'prix_nourriture': 0.05,
            'prix_cage': 12.00,
            'prix_vente_lapin': 15.00,
            'conso_2_mois': 200.0,
            'conso_3_mois_et_plus': 300.0,
            'age_min_gravide': 4,
            'age_max_gravide': 24,
            'duree_gestation': 1,
            'nb_max_par_portee': 8,
            'nb_max_individus_par_cage': 5,
            'seuil_surpopulation': 7
        })
        regle = Regle.objects.first()  # On suppose toujours qu’il n’y en a qu’une
        revenu_vente = (vendus_m + vendus_f) * regle.prix_vente_lapin
        cout_total = nourriture_achetee * regle.prix_nourriture + cages_achetees * regle.prix_cage
        argent_apres_vente = elevage.argent + revenu_vente

        if vendus_m > nb_males or vendus_f > nb_femelles:
            form.add_error(None, "Vous ne pouvez pas vendre plus de lapins que vous n'en avez.")
        elif cout_total > argent_apres_vente:
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
            resultats_tour = elevage.jouer_tour(nourriture_achetee, cages_achetees, vendus_m, vendus_f)
            form = Actions()  # Reset form après un tour
            
        #graphe
         
        nb_femelles_adultes = individus.filter(sexe='F', age__gte = 3).count()
        nb_males_adultes = individus.filter(sexe='M', age__gte = 3).count()
        nb_lapereaux = individus.filter(age__in = [0,2]).count()
        
        #dernier_tour = Tour.objects.filter(elevage = elevage).order_by('-numero').first()
        #nouveau_numero = dernier_tour.numero + 1 if dernier_tour else 1

        Tour.objects.create(
            elevage = elevage,
            numero = numero + 1,
            nb_femelles_adultes = nb_femelles_adultes,
            nb_males_adultes = nb_males_adultes,
            nb_lapereaux = nb_lapereaux
        )

        data = Tour.objects.filter(elevage = elevage).order_by('numero')  # Chronologique
        
        if data.exists(): 
            data_exists = True
            serialized_data = serializers.serialize("json", data)
        else:
            data_exists = True
            serialized_data = serializers.serialize("json", empty_data)

    context = {
        'elevage': elevage,
        'individus': individus,
        'form': form if not elevage.fin_du_jeu else None,
        'resultats_tour': resultats_tour if form_is_valid else None,
        'fin_du_jeu': elevage.fin_du_jeu,
        'lapins_vendus_m': vendus_m if form_is_valid else 0,
        'lapins_vendus_f': vendus_f if form_is_valid else 0,
        'data': serialized_data if data_exists else {},
    }
    return render(request, 'elevage/elevage.html', context)


def menu(request):
    return render(request, 'menu.html', {'hide_navbar': True})

def regles_jeu(request):
    return render(request, 'elevage/regles.html')

