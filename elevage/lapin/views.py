from django.shortcuts import render, redirect
from forms import ElevageForm

def nouveau(request):
    if request.method == 'POST':
        form = ElevageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('liste_elevages')  # Redirection à définir plus tard
    else:
        form = ElevageForm()
    return render(request, 'elevage/nouveau.html', {'form': form})