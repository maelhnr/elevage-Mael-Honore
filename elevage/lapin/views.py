from django.shortcuts import render, redirect
from .forms import ElevageForm
from .models import Elevage

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