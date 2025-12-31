from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from comptes.models import Utilisateur, Classe

class Cours(models.Model):
    titre = models.CharField(max_length=150)
    description = models.TextField()
    enseignant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,limit_choices_to={'role': 'enseignant'})
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, verbose_name="Classe", related_name='cours', null=True, blank=True)
    fichier_pdf = models.FileField(upload_to='cours/pdf/', verbose_name="Fichier PDF", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

    def inscrire_etudiants_classe(self):
        """Inscrit automatiquement tous les étudiants de la classe à ce cours"""
        if self.classe:
            etudiants_classe = Utilisateur.objects.filter(classe=self.classe, role='etudiant')
            for etudiant in etudiants_classe:
                Inscription.objects.get_or_create(
                    cours=self,
                    etudiant=etudiant
                )


class Inscription(models.Model):
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    etudiant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,limit_choices_to={'role': 'etudiant'})
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cours', 'etudiant')

    def __str__(self):
        return f"{self.etudiant.username} - {self.cours.titre}"


# Signal pour inscrire automatiquement les étudiants de la classe lors de la création d'un cours
@receiver(post_save, sender=Cours)
def inscrire_etudiants_automatiquement(sender, instance, created, **kwargs):
    """Inscrit automatiquement tous les étudiants de la classe au cours"""
    if created and instance.classe:
        instance.inscrire_etudiants_classe()
