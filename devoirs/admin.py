from django.contrib import admin
from .models import Devoir, Soumission


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display = ('titre', 'cours', 'deadline', 'created_at')
    list_filter = ('created_at', 'deadline', 'cours')
    search_fields = ('titre', 'description', 'cours__titre')
    date_hierarchy = 'created_at'


@admin.register(Soumission)
class SoumissionAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'devoir', 'date_soumission', 'statut')
    list_filter = ('date_soumission', 'devoir')
    search_fields = ('etudiant__username', 'devoir__titre')
    date_hierarchy = 'date_soumission'
    readonly_fields = ('statut',)
