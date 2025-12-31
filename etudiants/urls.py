from django.urls import path
from .views import (
    etudiant_login,
    dashboard_etudiant,
    mes_cours,
    detail_cours,
    mes_devoirs,
    soumettre_devoir,
    mes_notes,
    mes_soumissions,
)

urlpatterns = [
    path('login/', etudiant_login, name='etudiant_login'),
    path('', dashboard_etudiant, name='dashboard_etudiant'),
    path('mes-cours/', mes_cours, name='mes_cours'),
    path('cours/<int:cours_id>/', detail_cours, name='detail_cours'),
    path('mes-devoirs/', mes_devoirs, name='mes_devoirs'),
    path('soumettre-devoir/<int:devoir_id>/', soumettre_devoir, name='soumettre_devoir'),
    path('mes-notes/', mes_notes, name='mes_notes'),
    path('mes-soumissions/', mes_soumissions, name='mes_soumissions'),
]

