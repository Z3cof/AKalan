from django.contrib import admin
from .models import Cours, Inscription


@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = ('titre', 'enseignant', 'created_at')
    list_filter = ('created_at', 'enseignant')
    search_fields = ('titre', 'description', 'enseignant__username')
    date_hierarchy = 'created_at'


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'cours', 'date_inscription')
    list_filter = ('date_inscription', 'cours')
    search_fields = ('etudiant__username', 'cours__titre')
    date_hierarchy = 'date_inscription'
