from django.db import models
from random import randint, choice


class Elevage(models.Model):
    
    # Choix de la difficulté
    DIFFICULTE_CHOICES = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]
    difficulte = models.CharField(max_length=10, choices=DIFFICULTE_CHOICES, default='moyen')
    
    nom_joueur = models.CharField(max_length=100)
    nombre_males = models.PositiveIntegerField(default=0)
    nombre_femelles = models.PositiveIntegerField(default=0)
    quantite_nourriture = models.PositiveIntegerField(default=0)  # en grammes
    nombre_cages = models.PositiveIntegerField(default=0)
    argent = models.DecimalField(max_digits=10, decimal_places=2)
    date_creation = models.DateTimeField(auto_now_add=True)
    tour = models.PositiveIntegerField(default=0)
    fin_du_jeu = models.BooleanField(default=False)


    def __str__(self):
        return f"Élevage de {self.nom_joueur} - Créé le {self.date_creation.strftime('%d/%m/%Y')}"
    
    def jouer_tour(self, nourriture_achetee, cages_achetees, vendus_m, vendus_f):
        regle = Regle.objects.first()  # On suppose qu'il n'y en a qu'une
        self.tour += 1
        self.save()
        
        #Vente lapins
        revenu = (vendus_m + vendus_f) * regle.prix_vente_lapin
        self.argent += revenu

        # Appliquer les achats
        self.quantite_nourriture += nourriture_achetee 
        self.nombre_cages += cages_achetees
        self.argent -= nourriture_achetee * regle.prix_nourriture + cages_achetees * regle.prix_cage
        self.save()

        individus = self.individus.filter(etat__in=['P', 'G']) # Tous les vivants

        morts_faim = []
        morts_maladie = []
        naissances = []
        
        # Vieillissement des individus
        for individu in individus:
            individu.age += 1
            individu.save()
            
        
        
        # Gestion de la santé
        for individu in self.individus.filter(etat__in=['P', 'G'], age__gt=0):
            if individu.sante is not None and individu.elevage is not None:
                individu.sante.evolution()
                
        vivants = self.individus.filter(etat__in=['P', 'G'])
        for individu in vivants:
            sante = individu.sante  # Accès direct grâce à la relation OneToOne
            if sante.vivant == False :
                individu.etat = 'M'
                individu.save()
                morts_maladie.append(individu)
                    
            
        # Nourriture : calcul de la consommation et mort si pénurie
        individus = self.individus.filter(etat__in=['P', 'G'])
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
        vivants = self.individus.filter(etat__in=['P', 'G'])
        adultes_et_jeunes = vivants.exclude(age__in=[0, 1, 2])
        
        if adultes_et_jeunes.count() > self.nombre_cages * regle.seuil_surpopulation:
            for individu in vivants:
                if individu.age > 1 and randint(1, 100) <= 30:  # 30% de chance de mourir
                    individu.etat = 'M'
                    individu.save()
                    morts_maladie.append(individu)

        # Gestation : accouchement des femelles gravides
        femelles_gravides = self.individus.filter(sexe='F', etat='G')
        
        for femelle in femelles_gravides:
            nb_petits = randint(1, regle.nb_max_par_portee)
            for _ in range(nb_petits):
                sexe = choice(['M', 'F'])
                bebe = Individu.objects.create(
                    elevage=self,
                    age=0,
                    sexe=sexe,
                    etat='P',
                )
                bebe.save()
                naissances.append(bebe)
                
            # La femelle n'est plus gravide
            femelle.etat = 'P'
            femelle.save()
            
        
        # Nouvelle gestation
        femelles_potentielles = self.individus.filter(
            sexe='F',
            etat='P',
            age__gte=regle.age_min_gravide,
            age__lte=regle.age_max_gravide
        )
            
        nb_males_adultes = self.individus.filter(sexe='M', etat='P', age__gte=3).count()
        if nb_males_adultes > 0:
           for femelle in femelles_potentielles:
                if randint(1, 100) <= 70:  # 70% de chance de tomber enceinte
                    femelle.etat = 'G'
                    femelle.save()
        
        if self.individus.filter(etat__in=['P', 'G']).count() == 0:
            self.fin_du_jeu = True
            self.save()


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
    sante = models.OneToOneField('Sante', on_delete=models.CASCADE, related_name='individu_sante', null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Sauvegarder d'abord pour avoir un ID
        if not hasattr(self, 'sante_individu') or not self.sante_individu:
            sante = Sante.objects.create(individu=self, malade=False, niveau_sante=100)
            self.sante = sante
            super().save(update_fields=['sante'])  # Met à jour le lien sans refaire tout

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



class Sante(models.Model):
    malade = models.BooleanField(default=False)
    individu = models.OneToOneField('Individu', on_delete=models.CASCADE, related_name='sante_individu', null=False)
    niveau_sante = models.IntegerField(default=100)
    vivant = models.BooleanField(default=True)
    
    def is_guerir(self):
        self.niveau_sante = 100
        self.save()  # Sauvegarder après modification
        
    def is_malade(self):
        self.niveau_sante = 0
        self.save()  # Sauvegarder après modification
        
    def is_falling(self):
        if self.niveau_sante >= 20 :
            self.niveau_sante -= 20
        else :
            self.niveau_sante =0
        self.save()  # Sauvegarder après modification
    
    def is_recovering(self):
        if self.niveau_sante >= 20 :
            self.niveau_sante += 20
        else :
            self.niveau_sante =0
        self.save()  # Sauvegarder après modification
        
    def evolution(self):
        individu = self.individu  # Accéder à l'individu lié à cette instance
        regle = Regle.objects.first()
        elevage = individu.elevage

        # Probabilités en fonction de la difficulté
        prob_maladie, prob_guerison = 0, 0
        if elevage.difficulte == 'facile':
            prob_maladie, prob_guerison = 0.1, 0.7  # 10% de chance de tomber malade, 70% de chance de guérir
        elif elevage.difficulte == 'moyen':
            prob_maladie, prob_guerison = 0.3, 0.5  # 30% de chance de tomber malade, 50% de chance de guérir
        elif elevage.difficulte == 'difficile':
            prob_maladie, prob_guerison = 0.5, 0.3  # 50% de chance de tomber malade, 30% de chance de guérir

        # Nombre d'individus vivants et calcul de densité
        individus_vivants = elevage.individus.filter(etat__in=['P', 'G'])
        nb_individus = individus_vivants.count()
        densite = nb_individus / elevage.nombre_cages if elevage.nombre_cages > 0 else nb_individus

        # Risques et chances basées sur la densité
        risque_maladie = max(0, (densite - regle.nb_max_individus_par_cage) * 50)  # Risque basé sur la densité
        chance_guerison = max(0, (regle.nb_max_individus_par_cage - densite) * 15)  # Chance de guérison
        
        # 1 seul jour pour survivre une fois malade plus d'1mois
        if self.malade == True : 
            self.vivant = False

        # Application des probabilités
        if randint(1, 100) <= int(chance_guerison * 100):  # Probabilité de guérison
            self.is_recovering()
            if randint(1, 100) <= int(prob_guerison * 100):  # Guérison
                self.is_guerir()

        if randint(1, 100) <= int(risque_maladie * 100):  # Probabilité de maladie
            self.is_falling()
            if randint(1, 100) <= int(prob_maladie * 100):  # Maladie
                self.is_malade()


        




