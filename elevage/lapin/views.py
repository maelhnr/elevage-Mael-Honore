from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ElevageForm, Actions, SignUpForm
from .models import Elevage, Individu, Regle
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages


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
    if elevage.utilisateur != request.user and not request.user.is_superuser: # sécurité accès élevage
        return HttpResponseForbidden("Vous n'avez pas accès à cet élevage.")
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