from django.db import models

class Elevage(models.Model):
    nom_joueur = models.CharField(max_length=100)
    nombre_males = models.PositiveIntegerField(default=0)
    nombre_femelles = models.PositiveIntegerField(default=0)
    quantite_nourriture = models.PositiveIntegerField(default=0)  # en grammes
    nombre_cages = models.PositiveIntegerField(default=0)
    argent = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Élevage de {self.nom_joueur} - Créé le {self.date_creation.strftime('%d/%m/%Y')}"
    
class Individu(models.Model):
    SEXE_CHOICES = [
        ('M', 'Mâle'),
        ('F', 'Femelle'),
    ]
    ETAT_CHOICES = [
        ('present', 'Présent'),
        ('vendu', 'Vendu'),
        ('mort', 'Mort'),
        ('gravide', 'Gravide'),
    ]
    
    elevage = models.ForeignKey(Elevage, on_delete=models.CASCADE, related_name="individus")
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    age = models.IntegerField()  # en mois
    etat = models.CharField(max_length=10, choices=ETAT_CHOICES, default='present')
    
    def __str__(self):
        return f"{self.sexe} - {self.age} mois - {self.etat}"
    


