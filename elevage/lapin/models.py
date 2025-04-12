from django.db import models
from random import randint, choice


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
    
    def jouer_tour(self, nourriture_achetee, cages_achetees):
        regle = Regle.objects.first()  # On suppose qu'il n'y en a qu'une

        # Appliquer les achats
        self.quantite_nourriture += nourriture_achetee
        self.nombre_cages += cages_achetees
        self.argent -= nourriture_achetee * regle.prix_nourriture + cages_achetees * regle.prix_cage
        self.save()

        individus = self.individu_set.filter(etat__in=['P', 'G']) # Tous les vivants

        morts_faim = []
        morts_maladie = []
        naissances = []
        
        # Vieillissement des individus
        for individu in individus:
            individu.age += 1
            individu.save()
            
         # Nourriture : calcul de la consommation et mort si pénurie
        individus = self.individu_set.filter(etat__in=['P', 'G'])
        for individu in individus:
            if individu.age == 1:
                consommation = 0  # lait maternel
            elif individu.age == 2:
                consommation = regle.conso_2_mois
            else:
                consommation = regle.conso_3_mois_et_plus

            if self.quantite_nourriture >= consommation:
                self.quantite_nourriture -= consommation
            else:
                individu.etat = 'M'  # Mort
                individu.save()
                morts_faim.append(individu)

        self.save()

        # Surpopulation
        vivants = self.individu_set.filter(etat__in=['P', 'G'])
        adultes_et_jeunes = vivants.exclude(age__in=[0, 1, 2])
        
        if adultes_et_jeunes.count() > self.nombre_cages * regle.seuil_surpopulation:
            for individu in vivants:
                if individu.age > 1 and randint(1, 100) <= 30:  # 30% de chance de mourir
                    individu.etat = 'M'
                    individu.save()
                    morts_maladie.append(individu)

        # Gestation : accouchement des femelles gravides
        femelles_gravides = self.individu_set.filter(sexe='F', etat='G')
        
        for femelle in femelles_gravides:
            nb_petits = randint(1, regle.nb_max_par_portee)
            for _ in range(nb_petits):
                sexe = choice(['M', 'F'])
                bebe = Individu.objects.create(
                    elevage=self,
                    age=0,
                    sexe=sexe,
                    etat='P'
                )
                naissances.append(bebe)
                
            # La femelle n'est plus gravide
            femelle.etat = 'P'
            femelle.save()
            
        
             # Nouvelle gestation
            femelles_potentielles = self.individu_set.filter(
                sexe='F',
                etat='P',
                age__gte=regle.age_min_gravide,
                age__lte=regle.age_max_gravide
            )
            
            nb_males_adultes = self.individu_set.filter(sexe='M', etat='P', age__gte=regle.age_min_gravide).count()
            if nb_males_adultes > 0:
                for femelle in femelles_potentielles:
                    if randint(1, 100) <= 70:  # 70% de chance de tomber enceinte
                        femelle.etat = 'G'
                        femelle.save()

        return {
            'morts_faim': morts_faim,
            'morts_maladie': morts_maladie,
            'naissances': naissances
        }
    
class Individu(models.Model):
    class Sexe(models.TextChoices):
        MALE = 'M', 'Mâle'
        FEMELLE = 'F', 'Femelle'

    class Etat(models.TextChoices):
        PRESENT = 'P', 'Présent'
        VENDU = 'V', 'Vendu'
        MORT = 'M', 'Mort'
        GRAVIDE = 'G', 'Gravide'  # Pour les femelles enceintes

    elevage = models.ForeignKey('Elevage', on_delete=models.CASCADE, related_name='individus')
    sexe = models.CharField(max_length=1, choices=Sexe.choices)
    age = models.PositiveIntegerField(help_text="Âge en mois")
    etat = models.CharField(max_length=1, choices=Etat.choices)

    def __str__(self):
        return f"{self.get_sexe_display()} - {self.age} mois - {self.get_etat_display()}"


class Regle(models.Model):
    # Prix
    prix_nourriture = models.DecimalField(max_digits=5, decimal_places=3, help_text="Prix au g de nourriture")
    prix_cage = models.DecimalField(max_digits=5, decimal_places=2)
    prix_vente_lapin = models.DecimalField(max_digits=5, decimal_places=2)

    # Consommation
    conso_2_mois = models.DecimalField(max_digits=6, decimal_places=2, help_text="Conso en g/mois pour un lapin de 2 mois")
    conso_3_mois_et_plus = models.DecimalField(max_digits=6, decimal_places=2, help_text="Conso en g/mois à partir de 3 mois")

    # Reproduction
    age_min_gravide = models.IntegerField(help_text="Âge minimum (mois) pour être gravide")
    age_max_gravide = models.IntegerField(help_text="Âge maximum (mois) pour être gravide")
    duree_gestation = models.IntegerField(help_text="Durée en mois")
    nb_max_par_portee = models.IntegerField(help_text="Nombre max de lapereaux par portée")

    # Cages
    nb_max_individus_par_cage = models.IntegerField(help_text="Nombre normal d'individus par cage")
    seuil_surpopulation = models.IntegerField(help_text="Seuil à partir duquel il y a surpopulation")

    def __str__(self):
        return "Règle de jeu"



