from django.db import models
from cours.models import Cours
from comptes.models import Utilisateur

class Devoir(models.Model):
    cours = models.ForeignKey(Cours, on_delete=models.CASCADE)
    titre = models.CharField(max_length=150)
    description = models.TextField()
    deadline = models.DateTimeField()
    fichier = models.FileField(upload_to='devoirs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Soumission(models.Model):
    devoir = models.ForeignKey(Devoir, on_delete=models.CASCADE)
    etudiant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'etudiant'}
    )
    fichier = models.FileField(upload_to='soumissions/')
    date_soumission = models.DateTimeField(auto_now_add=True)

    @property
    def statut(self):
        if self.date_soumission > self.devoir.deadline:
            return "En retard"
        return "Soumis"

    class Meta:
        unique_together = ('devoir', 'etudiant')