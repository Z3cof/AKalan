from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Page d'accueil - redirige vers l'interface admin
    path('', views.home, name='home'),
    # Redirection de /admin/ vers /admin/login/
    path('admin/', RedirectView.as_view(url='/admin/login/', permanent=False), name='admin_redirect'),
    # Interface admin personnalisée
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/utilisateurs/', views.admin_utilisateurs, name='admin_utilisateurs'),
    path('admin/inviter-enseignant/', views.admin_inviter_enseignant, name='admin_inviter_enseignant'),
    path('admin/inviter-etudiant/', views.admin_inviter_etudiant, name='admin_inviter_etudiant'),
    path('admin/accepter-invitation/<str:token>/', views.accepter_invitation, name='accepter_invitation'),
    path('admin/classes/', views.admin_classes, name='admin_classes'),
    path('admin/ajouter-classe/', views.admin_ajouter_classe, name='admin_ajouter_classe'),
    path('admin/assigner_enseignant/', views.admin_assigner_enseignant, name='admin_assigner_enseignant'),
    path('admin/classe/<int:classe_id>/', views.admin_detail_classe, name='admin_detail_classe'),
    path('admin/classe/<int:classe_id>/modifier/', views.admin_modifier_classe, name='admin_modifier_classe'),
    path('admin/classe/<int:classe_id>/supprimer/', views.admin_supprimer_classe, name='admin_supprimer_classe'),
    path('admin/classe/<int:classe_id>/retirer-enseignant/<int:enseignant_id>/', views.admin_retirer_enseignant, name='admin_retirer_enseignant'),
    path('admin/cours/', views.admin_cours, name='admin_cours'),
    path('admin/cours/<int:cours_id>/', views.admin_detail_cours, name='admin_detail_cours'),
    path('admin/cours/<int:cours_id>/modifier/', views.admin_modifier_cours, name='admin_modifier_cours'),
    path('admin/cours/<int:cours_id>/supprimer/', views.admin_supprimer_cours, name='admin_supprimer_cours'),
    path('admin/devoirs/', views.admin_devoirs, name='admin_devoirs'),
    path('admin/devoir/<int:devoir_id>/', views.admin_detail_devoir, name='admin_detail_devoir'),
    path('admin/devoir/<int:devoir_id>/modifier/', views.admin_modifier_devoir, name='admin_modifier_devoir'),
    path('admin/devoir/<int:devoir_id>/supprimer/', views.admin_supprimer_devoir, name='admin_supprimer_devoir'),
    path('admin/utilisateur/<int:utilisateur_id>/', views.admin_detail_utilisateur, name='admin_detail_utilisateur'),
    path('admin/utilisateur/<int:utilisateur_id>/modifier/', views.admin_modifier_utilisateur, name='admin_modifier_utilisateur'),
    path('admin/utilisateur/<int:utilisateur_id>/supprimer/', views.admin_supprimer_utilisateur, name='admin_supprimer_utilisateur'),
    path('admin/deconnexion-automatique/', views.deconnexion_automatique, name='deconnexion_automatique'),
    path('enseignant/deconnexion-automatique/', views.deconnexion_automatique, name='deconnexion_automatique'),
    path('etudiant/deconnexion-automatique/', views.deconnexion_automatique, name='deconnexion_automatique'),
    path('enseignant/deconnexion-automatique/', views.deconnexion_automatique, name='deconnexion_automatique'),
]

