from copy import deepcopy
from django.db import models
from random import randint, choice
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, null=True)



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
            
        
        ####################################################################################
        
        # Gestion de la santé
        for individu in self.individus.filter(etat__in=['P', 'G'], age__gt=0):
            if individu.sante is not None and individu.elevage is not None:
                individu.sante.evolution()
                
        # Assassinat des lapins malades depuis plus d'1 mois
        vivants = self.individus.filter(etat__in=['P', 'G'])
        for individu in vivants:
            sante = individu.sante  # Accès direct grâce à la relation OneToOne
            if sante.vivant == False :
                individu.etat = 'M'
                individu.save()
                morts_maladie.append(individu)
                
        ####################################################################################
                    
            
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

    def parametres_elevage(self):
        regle = Regle.objects.first()
        individus = self.individus.filter(etat__in=['P', 'G'])
        
        concentration = len(individus)/self.nombre_cages
        
        consommation : float = 0.0
        for individu in individus:
            age = individu.age + 1
            if age == 1 :
                consommation = consommation + 0.0
            elif age == 2 :
                consommation = consommation + float(regle.conso_2_mois)
            else :
                consommation = consommation + float(regle.conso_3_mois_et_plus)
        return {
            'consommation': consommation,
            'concentration': concentration,
            
        }

    
    def simulation_sans_action(self):   
        regle = Regle.objects.first()
        quantite_nourriture = float(self.quantite_nourriture)
        nombre_cages = self.nombre_cages
        individus = self.individus.filter(etat__in=['P', 'G'])
        
        morts_faim = 0
        morts_maladie = 0
        naissances = 0
        
        #Nourriture
        for individu in individus:
            age = individu.age + 1
            if age == 1:
                conso = 0.0
            elif age == 2:
                conso = float(regle.conso_2_mois)
            else :
                conso = float(regle.conso_3_mois_et_plus)
            
            if quantite_nourriture >= conso:
                quantite_nourriture = quantite_nourriture - float(conso)
            else:
                morts_faim += 1
        
        # Surpopulation
        vivants = individus.filter(etat__in=['P', 'G'],age__gte=3)
        if len(vivants) > nombre_cages * regle.seuil_surpopulation:
            morts_maladie = int( len(vivants)*0.3 )
        
        # Accouchement des femelles gravides
        femelles_gravides = individus.filter(etat__in=['G'])
        for femelle in femelles_gravides:
            nb_petits = int((1 + regle.nb_max_par_portee)/2)
            naissances = naissances + nb_petits
        naissances = int(naissances)
        
        return {
        'morts_faim': morts_faim,
        'morts_maladie': morts_maladie,
        'naissances': naissances,
        'total_vivants_apres': len(individus) - morts_faim - morts_maladie + naissances,
        'nourriture_restante': quantite_nourriture
    }

    def prevision_avec_actions(self, nourriture_achetee, cages_achetees, vendus_m, vendus_f, nb_tours=3):
        regle = Regle.objects.first()

        nourriture = float(self.quantite_nourriture)
        cages = self.nombre_cages
        argent = float(self.argent)

        individus = [deepcopy(ind) for ind in self.individus.filter(etat__in=['P', 'G'])]

        previsions = []

        for tour in range(nb_tours):
            # Met à jour la liste des vivants
            vivants = [ind for ind in individus if ind.etat in ['P', 'G']]
            morts_faim = 0
            morts_maladie = []
            naissances = 0
            nouvelles_gestations = 0

            males_disponibles = [i for i in vivants if i.sexe == 'M']
            femelles_disponibles = [i for i in vivants if i.sexe == 'F']
            nb_vendus_m = min(vendus_m, len(males_disponibles))
            nb_vendus_f = min(vendus_f, len(femelles_disponibles))

            for i in range(nb_vendus_m):
                males_disponibles[i].etat = 'V'
            for i in range(nb_vendus_f):
                femelles_disponibles[i].etat = 'V'

            revenu = (nb_vendus_m + nb_vendus_f) * float(regle.prix_vente_lapin)
            argent += revenu

            nourriture += nourriture_achetee
            cages += cages_achetees
            argent -= nourriture_achetee * float(regle.prix_nourriture) + cages_achetees * float(regle.prix_cage)

            for ind in vivants:
                ind.age += 1

            for ind in vivants:
                if ind.age == 1:
                    conso = 0.0
                elif ind.age == 2:
                    conso = float(regle.conso_2_mois)
                else:
                    conso = float(regle.conso_3_mois_et_plus)

                if nourriture >= conso:
                    nourriture -= conso
                else:
                    ind.etat = 'M'
                    morts_faim += 1
                    
            vivants_adulte = [ind for ind in individus if ind.etat in ['P', 'G'] and ind.age>=3]
            if len(vivants) > cages * regle.seuil_surpopulation:
                nb_surplus = int(len(vivants) * 0.30)
                for ind in vivants[:nb_surplus]:
                    ind.etat = 'M'
                    morts_maladie.append(ind)

            for femelle in [ind for ind in individus if ind.etat == 'G']:
                nb_petits = int((regle.nb_max_par_portee + 1) / 2)
                for _ in range(nb_petits):
                    sexe = choice(['M', 'F'])
                    bebe = deepcopy(femelle)
                    bebe.sexe = sexe
                    bebe.age = 0
                    bebe.etat = 'P'
                    individus.append(bebe)
                    naissances += 1
                femelle.etat = 'P'

            femelles_reproductrices = [
                ind for ind in individus
                if ind.sexe == 'F' and ind.etat == 'P' and regle.age_min_gravide <= ind.age <= regle.age_max_gravide
            ]
            nb_males_adultes = sum(1 for ind in individus if ind.sexe == 'M' and ind.etat == 'P' and ind.age >= 3)

            if nb_males_adultes > 0:
                for femelle in femelles_reproductrices:
                    if randint(1, 100) <= 70:
                        femelle.etat = 'G'
                        nouvelles_gestations += 1
            vivants_final = [ind for ind in individus if ind.etat in ['P', 'G']]
            concentration = len(vivants_final) / max(1, cages)

            previsions.append({
                'tour': tour + 1,
                'vivants_apres': len(vivants_final),
                'morts_faim': morts_faim,
                'morts_maladie': len(morts_maladie),
                'naissances': naissances,
                'nouvelles_gestations': nouvelles_gestations,
                'nourriture_restante': round(nourriture, 2),
                'argent_apres': round(argent, 2),
                'concentration_apres': round(concentration, 2),
            })
        return previsions
    
    def propositions_optimisees(self):
        regle = Regle.objects.first()
        nourriture = float(self.quantite_nourriture)
        cages = self.nombre_cages
        argent = float(self.argent)
        individus = [deepcopy(ind) for ind in self.individus.filter(etat__in=['P', 'G'])]    
        
        #Nourriture
        achat_nourriture = 0
        consommation : float = 0.0
        for individu in individus:
            age = individu.age + 1
            if age == 1 :
                consommation = consommation + 0.0
            elif age == 2 :
                consommation = consommation + float(regle.conso_2_mois)
            else :
                consommation = consommation + float(regle.conso_3_mois_et_plus)
        if consommation > nourriture :
            achat_nourriture = consommation - nourriture
        
        #Cages
        achat_cages = 0
        concentration = len(individus)/self.nombre_cages
        if concentration > regle.seuil_surpopulation :
            achat_cages = int(len(individus)/regle.seuil_surpopulation) + 1 - self.nombre_cages
       
       #Ventes de lapins surpopulation
        vente_lapins = 0
        if concentration > regle.seuil_surpopulation :
            vente_lapins = len(individus) - regle.seuil_surpopulation * self.nombre_cages
        
        return {
        'achat_nourriture': achat_nourriture,
        'achat_cages': achat_cages,
        'vente_lapins': vente_lapins,
        }
        
    def indicateurs_cles(self):
        regle = Regle.objects.first()

        present = [deepcopy(ind) for ind in self.individus.filter(etat__in=['P'])]
        gravide = [deepcopy(ind) for ind in self.individus.filter(etat__in=['G'])]
        mort = [deepcopy(ind) for ind in self.individus.filter(etat__in=['M'])]
        vendu = [deepcopy(ind) for ind in self.individus.filter(etat__in=['V'])]
        
        #taille de l'elevage
        taille = len(present) + len(gravide)
        #taux de mortalite
        taux_mortalite = len(mort) / (len(present) + len(gravide) + len(mort) + len(vendu))    
        #taux de vente
        taux_vente = len(vendu) / (len(present) + len(gravide) + len(mort) + len(vendu))    
        #taux de natalite
        #Moyenne age
        age_moyen = 0
        if (len(present) + len(gravide)) > 0:
            age_moyen = sum([ind.age for ind in present] + [ind.age for ind in gravide]) / (len(present) + len(gravide))
        else:
            age_moyen = 0
        #Occupation cages
        occupation = 0
        nb_cages = self.nombre_cages
        capacite = nb_cages * regle.seuil_surpopulation
        if nb_cages > 0 :
            occupation = taille / capacite
        else :
            occupation = 0
        return {
        'taille': taille,
        'taux_mortalite': taux_mortalite,
        'taux_vente': taux_vente,
        'age_moyen':age_moyen,
        'occupation': occupation,        
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
    

    def save(self, *args, **kwargs):
        created = not self.pk  # Vérifie si c'est une nouvelle instance
        super().save(*args, **kwargs)
        if created:  # Si nouvel individu, créez sa santé
            Sante.objects.create(individu=self,vacciné = False, malade=False, niveau_sante=100)
            
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

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_premium = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

# Création automatique du profil Client à la création d'un User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Client.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.client.save()

class Sante(models.Model):
    vacciné = models.BooleanField(default=False)
    # On va faire tober le lapin malade
    malade = models.BooleanField(default=False)
    individu = models.OneToOneField('Individu', on_delete=models.CASCADE, related_name='sante', null=False)
    # Niveau de santé de lapin, plus il diminue, plus il aura de chances de tomber malade
    niveau_sante = models.IntegerField(default=100)
    # S'il a déja été malade le mois dernier, il devra mourir
    vivant = models.BooleanField(default=True)
    
    def is_guerir(self):
        self.niveau_sante = 100
        self.malade = False
        self.save()  
        
    def is_malade(self):
        self.niveau_sante = 0
        self.malade = True
        self.save()  
        
    def is_falling(self):
        if self.niveau_sante >= 20 :
            self.niveau_sante -= 20
        else :
            self.niveau_sante = 0
        self.save()  
    
    def is_recovering(self):
        if self.niveau_sante <= 80 :
            self.niveau_sante += 20
        else :
            self.niveau_sante = 100
        self.save()  
        
    # FOnction d'évolution de santé des individus
        
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
        
        # Si le lapin est vacciné, il aura moins de chances de tomber malade
        if self.vacciné == False : # Non vacciné guerison_base = 0 et malade_base = 40
            # Risques et chances basées sur la densité
            risque_maladie = max(0, (densite - regle.nb_max_individus_par_cage) * 15 )  
            # + 15% par lapin en trop dans l'elevage
            chance_guerison = max(0, (regle.nb_max_individus_par_cage - densite) * 15)  
            # + 5% Chance de guérison par place liberée dans l'elevage
        elif self.vacciné == True : # Non vacciné guerison_base = 40 et malade_base = 10
            # Risques et chances basées sur la densité
            risque_maladie = max(10, (densite - regle.nb_max_individus_par_cage) * 15 )  
            # + 15% par lapin en trop dans l'elevage
            chance_guerison = max(40, (regle.nb_max_individus_par_cage - densite) * 15)  
            # + 5% Chance de guérison par place liberée dans l'elevage
        
        # 1 seul jour pour survivre une fois malade plus d'1mois
        if self.malade == True : 
            self.vivant = False
            
        # Tomber malade selon son niveau de santé
        if randint(1, 100) >= int(self.niveau_sante): 
            self.is_malade()

        # Application des probabilités
        if randint(1, 100) <= int(chance_guerison):  # Probabilité de guérison
            self.is_recovering()
            if randint(1, 100) <= int(prob_guerison * 100):  # Guérison basée sur la difficulté
                self.is_guerir()

        if randint(1, 100) <= int(risque_maladie * 100):  # Probabilité de maladie
            self.is_falling()
            if randint(1, 100) <= int(prob_maladie * 100):  # Maladie basée sur la difficulté
                self.is_malade()


        




