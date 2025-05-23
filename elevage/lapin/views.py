import json
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ElevageForm, Actions, SignUpForm, RessourcesBonusForm
from .models import Elevage, Individu, Regle, Tour
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core import serializers



@login_required
def nouveau(request):
    client = request.user.client
    elevages_actifs = Elevage.objects.filter(utilisateur=request.user, fin_du_jeu=False).count()
    limite = 1000 if client.is_premium else 3

    if elevages_actifs >= limite:
        messages.error(request, "Limite atteinte : vous ne pouvez posséder que 3 élevages actifs simultanément avec un compte Basic.")
        return redirect('liste_elevages')
        
    if request.method == 'POST':
        form = ElevageForm(request.POST)
        if form.is_valid():
            elevage = form.save(commit=False)
            elevage.utilisateur = request.user  # 👈 association à l'utilisateur connecté
            elevage.save()

            # Création automatique des individus
            nb_femelles = form.cleaned_data['nombre_femelles']
            nb_males = form.cleaned_data['nombre_males'] 

            for _ in range(nb_femelles):
                Individu.objects.create(
                    elevage=elevage,
                    sexe='F',
                    age=0,
                    etat='P',  # Présent
                )
                
            for _ in range(nb_males):
                Individu.objects.create(
                    elevage=elevage,
                    sexe='M',
                    age=0,
                    etat='P',  # Présent
                )
            individus = Individu.objects.filter(elevage=elevage,etat__in=['P', 'G'] )
            
            nb_femelles_adultes = individus.filter(sexe='F', age__gte = 3).count()
            nb_males_adultes = individus.filter(sexe='M', age__gte = 3).count()
            nb_lapereaux = individus.filter(age__in = [0,2]).count()
            
            Tour.objects.create(
            elevage = elevage,
            numero =  0,
            nb_femelles_adultes = nb_femelles_adultes,
            nb_males_adultes = nb_males_adultes,
            nb_lapereaux = nb_lapereaux,
            nb_naissances = 0,
            nb_mortalites = 0
            )  
            elevage.tour = 0
            elevage.save()  
            return redirect('detail_elevage', elevage_id=elevage.id)
    else:
        form = ElevageForm()

    return render(request, 'elevage/nouveau.html', {'form': form})


@login_required
def liste(request):
    query = request.GET.get('q', '')

    if request.user.is_superuser:
        elevages = Elevage.objects.all()
    else:
        elevages = Elevage.objects.filter(utilisateur=request.user)

    if query:
        elevages = elevages.filter(nom_joueur__icontains=query)

    elevages = elevages.order_by('-date_creation')

    # Compteur d'élevages actifs
    if request.user.is_authenticated and not request.user.is_superuser:
        client = request.user.client
        elevages_actifs = Elevage.objects.filter(utilisateur=request.user, fin_du_jeu=False).count()
        limite = "∞" if client.is_premium else 3
    else:
        elevages_actifs = None
        limite = None

    context = {
        'elevages': elevages,
        'query': query,
        'elevages_actifs': elevages_actifs,
        'limite': limite,
    }
    return render(request, 'elevage/liste.html', context)


@login_required
def elevage(request, elevage_id):
    elevage = get_object_or_404(Elevage, id=elevage_id)
    if elevage.utilisateur != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("Accès refusé.")

    # Initialisation du formulaire si premium et bonus pas encore utilisé
    form_bonus = None
    if hasattr(request.user, 'client') and request.user.client.is_premium:
        form_bonus = RessourcesBonusForm(request.POST or None)

        if request.method == 'POST' and 'bonus_submit' in request.POST:
            if elevage.a_ajoute_ressources_tour != elevage.tour:
                if form_bonus.is_valid():
                    bonus = form_bonus.cleaned_data['type_bonus']
                    if bonus == 'nourriture':
                        elevage.quantite_nourriture += 20000
                    elif bonus == 'cages':
                        elevage.nombre_cages += 1
                    elif bonus == 'argent':
                        elevage.argent += 500
                    elevage.a_ajoute_ressources_tour = elevage.tour
                    elevage.save()
                    return redirect('detail_elevage', elevage_id=elevage.id)

    individus = Individu.objects.filter(
    elevage=elevage,
    etat__in=['P', 'G'] 
    )
    form = Actions(request.POST or None)
    resultats_tour = None
    form_is_valid = request.method == "POST" and form.is_valid()
    
    data = Tour.objects.filter(elevage=elevage).order_by('numero')
    data_exists = data.exists()
    if data_exists:
        serialized_data = serializers.serialize("json", data)
    else:
        serialized_data = "[]"
    numero = elevage.tour
    ## graphe initial 
    
    
    vendus_m = 0
    vendus_f = 0
   
    if elevage.fin_du_jeu:
        form = None

    elif form_is_valid:
        # Extraction des données
        vendus_m = form.cleaned_data['lapins_males_vendus'] or 0
        vendus_f = form.cleaned_data['lapins_femelles_vendus'] or 0
        nourriture_achetee = form.cleaned_data['nourriture_achetee'] or 0
        cages_achetees = form.cleaned_data['cages_achetees'] or 0
        action = request.POST.get('action')
        if action == "prevision":
            prevision_3_tours = elevage.prevision_avec_actions(nourriture_achetee,cages_achetees,vendus_m,vendus_f)
            parametres = elevage.parametres_elevage()
            prevision = elevage.simulation_sans_action()
            proposition = elevage.propositions_optimisees()
            indicateurs = elevage.indicateurs_cles()
            context = {
                'elevage': elevage,
                'individus': individus,
                'form': form,
                'resultats_tour': resultats_tour,
                'fin_du_jeu': elevage.fin_du_jeu,
                'lapins_vendus_m': vendus_m,
                'lapins_vendus_f': vendus_f,
                'parametres': parametres,
                'prevision': prevision,
                'prevision_3_tours': prevision_3_tours,
                'proposition': proposition,
                'indicateurs': indicateurs,
                'data': serialized_data,
            }
            return render(request, 'elevage/elevage.html', context)
        elif action == "valider":
            # Vérification des actions et application du tour
            regle = Regle.objects.first()
            revenu_vente = (vendus_m + vendus_f) * regle.prix_vente_lapin
            cout_total = nourriture_achetee * regle.prix_nourriture + cages_achetees * regle.prix_cage
            argent_apres_vente = elevage.argent + revenu_vente

            if vendus_m > individus.filter(sexe='M').count() or vendus_f > individus.filter(sexe='F').count():
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
                nb_lapereaux = nb_lapereaux,
                nb_naissances = resultats_tour['naissances'],
                nb_mortalites = resultats_tour['mortalites']
            )

            
            # Mettre à jour les données du graphe après création du nouveau Tour
            data = Tour.objects.filter(elevage=elevage).order_by('numero')
            data_exists = data.exists()
            serialized_data = serializers.serialize("json", data) if data_exists else "[]"
            data_json = [
                {
                    'numero': tour.numero,
                    'naissances': tour.nb_naissances,
                    'mortalites': tour.nb_mortalites,
                }
            for tour in data
            ]
            
            parametres = elevage.parametres_elevage()
            prevision = elevage.simulation_sans_action()
            proposition = elevage.propositions_optimisees()
            indicateurs = elevage.indicateurs_cles()
            
            context = {
                'elevage': elevage,
                'individus': individus,
                'form': form if not elevage.fin_du_jeu else None,
                'resultats_tour': resultats_tour if form_is_valid else None,
                'fin_du_jeu': elevage.fin_du_jeu,
                'lapins_vendus_m': vendus_m if form_is_valid else 0,
                'lapins_vendus_f': vendus_f if form_is_valid else 0,
                'parametres': parametres,
                'prevision': prevision,
                'prevision_3_tours': None,
                'proposition': proposition,
                'indicateurs': indicateurs,
                'data': serialized_data,
                'form_bonus': form_bonus,
                'courbes': json.dumps(data_json),

            }
            return render(request, 'elevage/elevage.html', context)

        else :
        
            parametres = elevage.parametres_elevage()
            prevision = elevage.simulation_sans_action()
            proposition = elevage.propositions_optimisees()
            indicateurs = elevage.indicateurs_cles()
            
            context = {
                'elevage': elevage,
                'individus': individus,
                'form': form if not elevage.fin_du_jeu else None,
                'resultats_tour': resultats_tour if form_is_valid else None,
                'fin_du_jeu': elevage.fin_du_jeu,
                'lapins_vendus_m': vendus_m if form_is_valid else 0,
                'lapins_vendus_f': vendus_f if form_is_valid else 0,
                'parametres': parametres,
                'prevision': prevision,
                'prevision_3_tours': None,
                'proposition': proposition,
                'indicateurs': indicateurs,
                'data': serialized_data,
                'form_bonus': form_bonus,
            }
            return render(request, 'elevage/elevage.html', context)
        
    else :
        
        parametres = elevage.parametres_elevage()
        prevision = elevage.simulation_sans_action()
        proposition = elevage.propositions_optimisees()
        indicateurs = elevage.indicateurs_cles()
        
        context = {
            'elevage': elevage,
            'individus': individus,
            'form': form if not elevage.fin_du_jeu else None,
            'resultats_tour': resultats_tour if form_is_valid else None,
            'fin_du_jeu': elevage.fin_du_jeu,
            'lapins_vendus_m': vendus_m if form_is_valid else 0,
            'lapins_vendus_f': vendus_f if form_is_valid else 0,
            'parametres': parametres,
            'prevision': prevision,
            'prevision_3_tours': None,
            'proposition': proposition,
            'indicateurs': indicateurs,
            'data': serialized_data,
            'form_bonus': form_bonus,
        }
        return render(request, 'elevage/elevage.html', context)

        
            
        
    context = {
        'elevage': elevage,
        'individus': individus,
        'form': form if not elevage.fin_du_jeu else None,
        'resultats_tour': resultats_tour if form_is_valid else None,
        'fin_du_jeu': elevage.fin_du_jeu,
        'lapins_vendus_m': vendus_m if form_is_valid else 0,
        'lapins_vendus_f': vendus_f if form_is_valid else 0,
        'data': serialized_data,
        'form_bonus': form_bonus,
    }
    return render(request, 'elevage/elevage.html', context)


def menu(request):
    return render(request, 'menu.html', {'hide_navbar': True})

def regles_jeu(request):
    return render(request, 'elevage/regles.html')


def gestion_lapins(request, elevage_id):
    elevage = get_object_or_404(Elevage, id=elevage_id)
    individus = Individu.objects.filter(
        elevage=elevage,
        etat__in=['P', 'G'],
        sante__vivant=True
    ).select_related('sante')
    
    if request.method == 'POST':
        lapin_id = request.POST.get('lapin_id')
        action = request.POST.get('action')
        
        if lapin_id and action:
            lapin = get_object_or_404(Individu, id=lapin_id, elevage=elevage)
            
            # Nouveau cas: vaccination
            if action == 'vacciner':
                if not lapin.sante.vacciné:
                    if elevage.argent >= 120:
                        lapin.sante.vacciné = True
                        elevage.argent -= 120
                        lapin.sante.save()
                        elevage.save()

                return redirect('gestion_lapins', elevage_id=elevage.id)
            
            # Ancienne logique de soin
            if action in ['total', 'partiel'] and (lapin.sante.malade or lapin.sante.niveau_sante <= 0):
                cout = 10 if action == 'total' else 5
                
                if elevage.argent >= cout:
                    if action == 'total':
                        lapin.sante.niveau_sante = 100
                    else:
                        lapin.sante.niveau_sante = min(100, lapin.sante.niveau_sante + 50)
                    
                    lapin.sante.malade = False
                    elevage.argent -= cout
                    lapin.sante.save()
                    elevage.save()
                
                return redirect('gestion_lapins', elevage_id=elevage.id)

    return render(request, 'elevage/gestion_lapins.html', {
        'elevage': elevage,
        'individus': individus,
        'prix_vaccination': 120,
    })

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            login(request, user)
            return redirect('menu')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def premium_info(request):
    return render(request, 'elevage/premium_info.html')

