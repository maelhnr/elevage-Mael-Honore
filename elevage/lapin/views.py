from django.shortcuts import render, redirect, get_object_or_404
from .forms import ElevageForm
from .models import Elevage, Individu

def nouveau(request):
    if request.method == 'POST':
        form = ElevageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nouveau_elevage')  # Redirection à définir plus tard
    else:
        form = ElevageForm()
    return render(request, 'elevage/nouveau.html', {'form': form})

def liste(request):
    elevages = Elevage.objects.all().order_by('-date_creation')
    return render(request, 'elevage/liste.html', {'elevages': elevages})

def elevage(request, elevage_id):
    elevage = get_object_or_404(Elevage, id=elevage_id)
    individus = Individu.objects.filter(elevage=elevage, etat='P')  # On affiche uniquement les vivants
    return render(request, 'elevage/elevage.html', {
        'elevage': elevage,
        'individus': individus,
    })