from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Avg, Count, Q
from cours.models import Cours, Inscription
from devoirs.models import Devoir, Soumission
from comptes.models import Utilisateur, Classe, Note


def is_etudiant(user):
    """Vérifie si l'utilisateur est un étudiant"""
    return user.is_authenticated and user.role == 'etudiant'


def etudiant_login(request):
    """Page de connexion pour l'étudiant"""
    if request.user.is_authenticated and request.user.role == 'etudiant':
        # Rediriger vers la page demandée ou le dashboard
        next_url = request.GET.get('next', 'etudiants:dashboard_etudiant')
        return redirect(next_url)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = Utilisateur.objects.get(username=username)
            if user.check_password(password) and user.role == 'etudiant':
                login(request, user)
                messages.success(request, f'Bienvenue, {user.username}!')
                # Rediriger vers la page demandée ou le dashboard
                next_url = request.POST.get('next') or request.GET.get('next', 'etudiants:dashboard_etudiant')
                # S'assurer que next_url est une URL valide pour l'étudiant
                if next_url and not next_url.startswith('/etudiant/') and not next_url.startswith('etudiants:'):
                    next_url = 'etudiants:dashboard_etudiant'
                return redirect(next_url)
            else:
                messages.error(request, 'Identifiants incorrects ou vous n\'êtes pas étudiant.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Identifiants incorrects.')
    
    context = {
        'next': request.GET.get('next', ''),
    }
    return render(request, 'etudiant/login.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def dashboard_etudiant(request):
    """Dashboard de l'étudiant"""
    etudiant = request.user
    
    # Récupérer les cours de la classe de l'étudiant
    cours_etudiant = Cours.objects.none()
    if etudiant.classe:
        try:
            cours_etudiant = Cours.objects.filter(classe=etudiant.classe).order_by('-created_at')
        except Exception:
            # Si le champ classe n'existe pas encore
            cours_etudiant = Cours.objects.none()
    
    # Récupérer les inscriptions de l'étudiant
    inscriptions = Inscription.objects.filter(etudiant=etudiant)
    cours_inscrits = [inscription.cours for inscription in inscriptions]
    
    # Récupérer les devoirs des cours de l'étudiant
    devoirs_etudiant = Devoir.objects.filter(cours__in=cours_inscrits).order_by('-deadline')
    
    # Récupérer les soumissions de l'étudiant
    soumissions = Soumission.objects.filter(etudiant=etudiant).order_by('-date_soumission')
    
    # Statistiques
    now = timezone.now()
    devoirs_en_retard = devoirs_etudiant.filter(deadline__lt=now)
    devoirs_a_venir = devoirs_etudiant.filter(deadline__gte=now)
    
    # Récupérer les notes de l'étudiant
    notes_etudiant = Note.objects.filter(etudiant=etudiant).order_by('-date_attribution')
    moyenne_generale = notes_etudiant.aggregate(Avg('note'))['note__avg']
    
    # Devoirs non soumis
    devoirs_non_soumis = []
    for devoir in devoirs_etudiant:
        if not Soumission.objects.filter(devoir=devoir, etudiant=etudiant).exists():
            devoirs_non_soumis.append(devoir)
    
    context = {
        'etudiant': etudiant,
        'total_cours': len(cours_inscrits),
        'total_devoirs': devoirs_etudiant.count(),
        'total_soumissions': soumissions.count(),
        'devoirs_en_retard': devoirs_en_retard.count(),
        'devoirs_a_venir': devoirs_a_venir.count(),
        'devoirs_non_soumis': len(devoirs_non_soumis),
        'cours_inscrits': cours_inscrits[:5],  # 5 derniers cours
        'devoirs_recents': devoirs_etudiant[:5],  # 5 derniers devoirs
        'soumissions_recentes': soumissions[:5],  # 5 dernières soumissions
        'notes_recentes': notes_etudiant[:5],  # 5 dernières notes
        'moyenne_generale': round(moyenne_generale, 2) if moyenne_generale else None,
        'now': now,
    }
    
    return render(request, 'etudiant/dashboard.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def mes_cours(request):
    """Afficher les cours de l'étudiant"""
    etudiant = request.user
    
    # Récupérer les cours de la classe de l'étudiant et s'assurer qu'il est inscrit
    cours_avec_stats = []
    if etudiant.classe:
        try:
            cours_classe = Cours.objects.filter(classe=etudiant.classe).order_by('-created_at')
            # Inscrire automatiquement l'étudiant aux cours de sa classe s'il n'est pas déjà inscrit
            for cours in cours_classe:
                inscription, created = Inscription.objects.get_or_create(
                    cours=cours,
                    etudiant=etudiant
                )
                
                nb_devoirs = Devoir.objects.filter(cours=cours).count()
                nb_soumissions = Soumission.objects.filter(devoir__cours=cours, etudiant=etudiant).count()
                
                cours_avec_stats.append({
                    'cours': cours,
                    'date_inscription': inscription.date_inscription,
                    'nb_devoirs': nb_devoirs,
                    'nb_soumissions': nb_soumissions,
                })
        except Exception:
            # Si le champ classe n'existe pas encore, utiliser les inscriptions existantes
            inscriptions = Inscription.objects.filter(etudiant=etudiant).order_by('-date_inscription')
            for inscription in inscriptions:
                cours = inscription.cours
                nb_devoirs = Devoir.objects.filter(cours=cours).count()
                nb_soumissions = Soumission.objects.filter(devoir__cours=cours, etudiant=etudiant).count()
                
                cours_avec_stats.append({
                    'cours': cours,
                    'date_inscription': inscription.date_inscription,
                    'nb_devoirs': nb_devoirs,
                    'nb_soumissions': nb_soumissions,
                })
    else:
        # Si l'étudiant n'a pas de classe, utiliser uniquement les inscriptions existantes
        inscriptions = Inscription.objects.filter(etudiant=etudiant).order_by('-date_inscription')
        for inscription in inscriptions:
            cours = inscription.cours
            nb_devoirs = Devoir.objects.filter(cours=cours).count()
            nb_soumissions = Soumission.objects.filter(devoir__cours=cours, etudiant=etudiant).count()
            
            cours_avec_stats.append({
                'cours': cours,
                'date_inscription': inscription.date_inscription,
                'nb_devoirs': nb_devoirs,
                'nb_soumissions': nb_soumissions,
            })
    
    context = {
        'etudiant': etudiant,
        'cours_avec_stats': cours_avec_stats,
        'total_cours': len(cours_avec_stats),
    }
    
    return render(request, 'etudiant/mes_cours.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def detail_cours(request, cours_id):
    """Afficher les détails d'un cours pour l'étudiant"""
    etudiant = request.user
    cours = get_object_or_404(Cours, id=cours_id)
    
    # Vérifier que l'étudiant est dans la classe du cours ou est inscrit
    peut_acceder = False
    if cours.classe and etudiant.classe == cours.classe:
        peut_acceder = True
        # S'assurer que l'étudiant est inscrit
        Inscription.objects.get_or_create(cours=cours, etudiant=etudiant)
    elif Inscription.objects.filter(cours=cours, etudiant=etudiant).exists():
        peut_acceder = True
    
    if not peut_acceder:
        messages.error(request, "Vous n'avez pas accès à ce cours.")
        return redirect('etudiants:mes_cours')
    
    # Récupérer les devoirs de ce cours
    devoirs = Devoir.objects.filter(cours=cours).order_by('deadline')
    
    # Pour chaque devoir, vérifier si l'étudiant a soumis
    devoirs_avec_statut = []
    now = timezone.now()
    for devoir in devoirs:
        soumission = Soumission.objects.filter(devoir=devoir, etudiant=etudiant).first()
        est_en_retard = now > devoir.deadline
        
        devoirs_avec_statut.append({
            'devoir': devoir,
            'soumission': soumission,
            'est_en_retard': est_en_retard,
            'peut_soumettre': not soumission and not est_en_retard,
        })
    
    context = {
        'cours': cours,
        'etudiant': etudiant,
        'devoirs_avec_statut': devoirs_avec_statut,
        'total_devoirs': len(devoirs_avec_statut),
        'now': now,
    }
    
    return render(request, 'etudiant/detail_cours.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def mes_devoirs(request):
    """Afficher tous les devoirs de l'étudiant"""
    etudiant = request.user
    
    # Récupérer les cours de l'étudiant
    inscriptions = Inscription.objects.filter(etudiant=etudiant)
    cours_inscrits = [inscription.cours for inscription in inscriptions]
    
    # Récupérer tous les devoirs de ces cours
    devoirs = Devoir.objects.filter(cours__in=cours_inscrits).order_by('deadline')
    
    # Pour chaque devoir, vérifier le statut
    now = timezone.now()
    devoirs_avec_statut = []
    for devoir in devoirs:
        soumission = Soumission.objects.filter(devoir=devoir, etudiant=etudiant).first()
        est_en_retard = now > devoir.deadline
        
        devoirs_avec_statut.append({
            'devoir': devoir,
            'soumission': soumission,
            'est_en_retard': est_en_retard,
            'peut_soumettre': not soumission and not est_en_retard,
        })
    
    context = {
        'etudiant': etudiant,
        'devoirs_avec_statut': devoirs_avec_statut,
        'total_devoirs': len(devoirs_avec_statut),
        'now': now,
    }
    
    return render(request, 'etudiant/mes_devoirs.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def soumettre_devoir(request, devoir_id):
    """Soumettre un devoir"""
    etudiant = request.user
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    # Vérifier que l'étudiant est dans la classe du cours ou est inscrit
    peut_acceder = False
    if devoir.cours.classe and etudiant.classe == devoir.cours.classe:
        peut_acceder = True
        # S'assurer que l'étudiant est inscrit
        Inscription.objects.get_or_create(cours=devoir.cours, etudiant=etudiant)
    elif Inscription.objects.filter(cours=devoir.cours, etudiant=etudiant).exists():
        peut_acceder = True
    
    if not peut_acceder:
        messages.error(request, "Vous n'avez pas accès à ce devoir.")
        return redirect('etudiants:mes_devoirs')
    
    # Vérifier si le devoir est déjà soumis
    soumission_existante = Soumission.objects.filter(devoir=devoir, etudiant=etudiant).first()
    if soumission_existante:
        messages.warning(request, "Vous avez déjà soumis ce devoir.")
        return redirect('etudiants:mes_devoirs')
    
    # Vérifier la date limite
    now = timezone.now()
    if now > devoir.deadline:
        messages.error(request, "La date limite de soumission est dépassée.")
        return redirect('etudiants:mes_devoirs')
    
    if request.method == 'POST':
        fichier = request.FILES.get('fichier')
        if not fichier:
            messages.error(request, "Veuillez sélectionner un fichier.")
            return render(request, 'etudiant/soumettre_devoir.html', {'devoir': devoir})
        
        # Créer la soumission
        Soumission.objects.create(
            devoir=devoir,
            etudiant=etudiant,
            fichier=fichier
        )
        messages.success(request, f'Devoir "{devoir.titre}" soumis avec succès!')
        return redirect('etudiants:mes_devoirs')
    
    context = {
        'devoir': devoir,
        'etudiant': etudiant,
        'now': now,
    }
    
    return render(request, 'etudiant/soumettre_devoir.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def mes_notes(request):
    """Afficher les notes de l'étudiant"""
    etudiant = request.user
    
    # Récupérer toutes les notes de l'étudiant
    notes = Note.objects.filter(etudiant=etudiant).order_by('-date_attribution')
    
    # Calculer les moyennes par devoir
    notes_par_devoir = {}
    for note in notes:
        devoir_nom = note.devoir.titre
        if devoir_nom not in notes_par_devoir:
            notes_par_devoir[devoir_nom] = []
        notes_par_devoir[devoir_nom].append(note)
    
    # Calculer la moyenne générale
    moyenne_generale = notes.aggregate(Avg('note'))['note__avg']
    
    # Calculer les moyennes par devoir
    moyennes_par_devoir = {}
    for devoir_nom, notes_devoir in notes_par_devoir.items():
        moyenne = sum(note.note for note in notes_devoir) / len(notes_devoir)
        moyennes_par_devoir[devoir_nom] = round(moyenne, 2)
    
    context = {
        'etudiant': etudiant,
        'notes': notes,
        'notes_par_devoir': notes_par_devoir,
        'moyenne_generale': round(moyenne_generale, 2) if moyenne_generale else None,
        'moyennes_par_devoir': moyennes_par_devoir,
        'total_notes': notes.count(),
    }
    
    return render(request, 'etudiant/mes_notes.html', context)


@login_required
@user_passes_test(is_etudiant, login_url='/etudiant/login/')
def mes_soumissions(request):
    """Afficher les soumissions de l'étudiant"""
    etudiant = request.user
    
    # Récupérer toutes les soumissions de l'étudiant
    soumissions = Soumission.objects.filter(etudiant=etudiant).order_by('-date_soumission')
    
    # Pour chaque soumission, vérifier le statut
    soumissions_avec_statut = []
    for soumission in soumissions:
        est_en_retard = soumission.date_soumission > soumission.devoir.deadline
        soumissions_avec_statut.append({
            'soumission': soumission,
            'est_en_retard': est_en_retard,
        })
    
    context = {
        'etudiant': etudiant,
        'soumissions_avec_statut': soumissions_avec_statut,
        'total_soumissions': len(soumissions_avec_statut),
    }
    
    return render(request, 'etudiant/mes_soumissions.html', context)

