from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta

class Classe(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la classe")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    enseignants = models.ManyToManyField(
        'Utilisateur',
        limit_choices_to={'role': 'enseignant'},
        verbose_name="Enseignants",
        related_name='classes_enseignees',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
    
    def get_nb_etudiants(self):
        """Retourne le nombre d'étudiants dans cette classe"""
        return self.utilisateur_set.filter(role='etudiant').count()
    
    def get_nb_enseignants(self):
        """Retourne le nombre d'enseignants dans cette classe"""
        return self.enseignants.count()


class Utilisateur(AbstractUser):
    ROLES_CHOICES = (
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('etudiant', 'Étudiant'),
    )

    role = models.CharField(max_length=20, choices=ROLES_CHOICES)
    classe = models.ForeignKey(
        Classe, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Classe"
    )
    
    def inscrire_aux_cours_classe(self):
        """Inscrit automatiquement l'étudiant aux cours de sa classe"""
        if self.role == 'etudiant' and self.classe:
            from cours.models import Cours, Inscription
            cours_classe = Cours.objects.filter(classe=self.classe)
            for cours in cours_classe:
                Inscription.objects.get_or_create(
                    cours=cours,
                    etudiant=self
                )


class Note(models.Model):
    """Modèle pour stocker les notes attribuées aux étudiants"""
    etudiant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'etudiant'},
        related_name='notes',
        verbose_name="Étudiant"
    )
    enseignant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'enseignant'},
        related_name='notes_attribuees',
        verbose_name="Enseignant"
    )
    devoir = models.ForeignKey(
        'devoirs.Devoir',
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name="Devoir",
        null=False,
        blank=False
    )
    note = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Note",
        help_text="Note sur 20"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire"
    )
    date_attribution = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'attribution"
    )
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        ordering = ['-date_attribution']
    
    def __str__(self):
        return f"{self.etudiant.username} - {self.note}/20 - {self.devoir.titre}"


class Invitation(models.Model):
    """Modèle pour gérer les invitations d'utilisateurs"""
    STATUT_CHOICES = (
        ('en_attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('expiree', 'Expirée'),
    )
    
    email = models.EmailField(verbose_name="Email")
    role = models.CharField(
        max_length=20,
        choices=Utilisateur.ROLES_CHOICES,
        verbose_name="Rôle"
    )
    classe = models.ForeignKey(
        Classe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Classe",
        help_text="Uniquement pour les étudiants"
    )
    token = models.CharField(max_length=64, unique=True, verbose_name="Token")
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en_attente',
        verbose_name="Statut"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_expiration = models.DateTimeField(verbose_name="Date d'expiration")
    date_acceptation = models.DateTimeField(null=True, blank=True, verbose_name="Date d'acceptation")
    cree_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invitations_creees',
        verbose_name="Créé par"
    )
    
    class Meta:
        verbose_name = "Invitation"
        verbose_name_plural = "Invitations"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Invitation {self.email} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        if not self.date_expiration:
            # Expiration dans 7 jours par défaut
            self.date_expiration = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    def est_expiree(self):
        """Vérifie si l'invitation est expirée"""
        return timezone.now() > self.date_expiration
    
    def est_valide(self):
        """Vérifie si l'invitation est valide (non expirée et en attente)"""
        return self.statut == 'en_attente' and not self.est_expiree()
    
    def accepter(self):
        """Marque l'invitation comme acceptée"""
        self.statut = 'acceptee'
        self.date_acceptation = timezone.now()
        self.save()


# Signal pour inscrire automatiquement un étudiant aux cours de sa classe lorsqu'il est assigné à une classe
@receiver(post_save, sender=Utilisateur)
def inscrire_etudiant_aux_cours(sender, instance, **kwargs):
    """Inscrit automatiquement un étudiant aux cours de sa classe lorsqu'il est assigné à une classe"""
    # Ne s'exécute que si l'utilisateur est un étudiant et a une classe
    if instance.role == 'etudiant' and instance.classe:
        instance.inscrire_aux_cours_classe()

