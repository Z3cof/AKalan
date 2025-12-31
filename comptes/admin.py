from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Note, Invitation


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Configuration de l'admin pour le modèle Utilisateur"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle personnalisé', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Rôle personnalisé', {'fields': ('role',)}),
    )


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Configuration de l'admin pour le modèle Note"""
    list_display = ('etudiant', 'enseignant', 'devoir', 'note', 'date_attribution')
    list_filter = ('enseignant', 'devoir', 'date_attribution')
    search_fields = ('etudiant__username', 'etudiant__email', 'enseignant__username', 'devoir__titre')
    readonly_fields = ('date_attribution',)
    date_hierarchy = 'date_attribution'


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    """Configuration de l'admin pour le modèle Invitation"""
    list_display = ('email', 'role', 'classe', 'statut', 'date_creation', 'date_expiration', 'cree_par')
    list_filter = ('role', 'statut', 'date_creation')
    search_fields = ('email', 'token')
    readonly_fields = ('token', 'date_creation', 'date_acceptation')
    date_hierarchy = 'date_creation'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Si on modifie un objet existant
            return self.readonly_fields + ('email', 'role', 'classe')
        return self.readonly_fields
