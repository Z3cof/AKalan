from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.db.models import Avg, Count
from cours.models import Cours, Inscription
from devoirs.models import Devoir, Soumission
from comptes.models import Utilisateur, Classe, Note
from .forms import CoursForm, DevoirForm, NoteForm


def is_enseignant(user):
    """Vérifie si l'utilisateur est un enseignant"""
    return user.is_authenticated and user.role == 'enseignant'


def enseignant_login(request):
    """Page de connexion pour l'enseignant"""
    if request.user.is_authenticated and request.user.role == 'enseignant':
        # Rediriger vers la page demandée ou le dashboard
        next_url = request.GET.get('next', 'enseignants:dashboard_enseignant')
        return redirect(next_url)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = Utilisateur.objects.get(username=username)
            if user.check_password(password) and user.role == 'enseignant':
                login(request, user)
                messages.success(request, f'Bienvenue, {user.username}!')
                # Rediriger vers la page demandée ou le dashboard
                next_url = request.POST.get('next') or request.GET.get('next', 'enseignants:dashboard_enseignant')
                # S'assurer que next_url est une URL valide pour l'enseignant
                if next_url and not next_url.startswith('/enseignant/') and not next_url.startswith('enseignants:'):
                    next_url = 'enseignants:dashboard_enseignant'
                return redirect(next_url)
            else:
                messages.error(request, 'Identifiants incorrects ou vous n\'êtes pas enseignant.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Identifiants incorrects.')
    
    context = {
        'next': request.GET.get('next', ''),
    }
    return render(request, 'enseignant/login.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def dashboard_enseignant(request):
    """Dashboard de l'enseignant"""
    enseignant = request.user
    
    # Statistiques
    # Utiliser try/except pour gérer le cas où le champ classe n'existe pas encore
    try:
        total_cours = Cours.objects.filter(enseignant=enseignant).count()
        cours = Cours.objects.filter(enseignant=enseignant).order_by('-created_at')
    except Exception:
        try:
            # Utiliser only() pour spécifier uniquement les champs qui existent
            total_cours = Cours.objects.filter(enseignant=enseignant).only('id', 'titre', 'description', 'enseignant_id', 'created_at').count()
            cours = Cours.objects.filter(enseignant=enseignant).only('id', 'titre', 'description', 'enseignant_id', 'created_at').order_by('-created_at')
        except Exception:
            total_cours = 0
            cours = Cours.objects.none()
    
    total_devoirs = Devoir.objects.filter(cours__enseignant=enseignant).count()
    total_soumissions = Soumission.objects.filter(devoir__cours__enseignant=enseignant).count()
    total_classes = enseignant.classes_enseignees.count()
    
    # Devoirs de l'enseignant
    devoirs = Devoir.objects.filter(cours__enseignant=enseignant).order_by('-deadline')
    
    # Devoirs en retard
    now = timezone.now()
    devoirs_en_retard = devoirs.filter(deadline__lt=now)
    devoirs_a_venir = devoirs.filter(deadline__gte=now)
    
    context = {
        'enseignant': enseignant,
        'total_cours': total_cours,
        'total_devoirs': total_devoirs,
        'total_soumissions': total_soumissions,
        'total_classes': total_classes,
        'cours': cours,
        'devoirs': devoirs,
        'devoirs_en_retard': devoirs_en_retard.count(),
        'devoirs_a_venir': devoirs_a_venir.count(),
        'now': now,
    }
    
    return render(request, 'enseignant/dashboard.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def ajouter_cours(request):
    """Ajouter un cours"""
    enseignant = request.user
    
    if request.method == 'POST':
        form = CoursForm(request.POST, request.FILES)
        if form.is_valid():
            cours = form.save(commit=False)
            cours.enseignant = enseignant
            
            # Vérifier que l'enseignant est assigné à la classe sélectionnée
            if enseignant not in cours.classe.enseignants.all():
                messages.error(request, "Vous n'êtes pas assigné à cette classe.")
                form.fields['classe'].queryset = enseignant.classes_enseignees.all()
                return render(request, 'enseignant/ajouter_cours.html', {'form': form})
            
            cours.save()
            
            # Inscrire automatiquement tous les étudiants de la classe
            if cours.classe:
                etudiants_classe = cours.classe.utilisateur_set.filter(role='etudiant')
                nb_inscrits = 0
                for etudiant in etudiants_classe:
                    inscription, created = Inscription.objects.get_or_create(
                        cours=cours,
                        etudiant=etudiant
                    )
                    if created:
                        nb_inscrits += 1
                
                if nb_inscrits > 0:
                    messages.success(request, f'Cours "{cours.titre}" ajouté avec succès! {nb_inscrits} étudiant(s) de la classe "{cours.classe.nom}" inscrit(s) automatiquement.')
                else:
                    messages.success(request, f'Cours "{cours.titre}" ajouté avec succès!')
            else:
                messages.success(request, f'Cours "{cours.titre}" ajouté avec succès!')
            
                return redirect('enseignants:mes_cours')
    else:
        form = CoursForm()
        # Filtrer les classes pour n'afficher que celles où l'enseignant est assigné
        form.fields['classe'].queryset = enseignant.classes_enseignees.all()
    
    return render(request, 'enseignant/ajouter_cours.html', {'form': form})


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def ajouter_devoir(request):
    """Ajouter un devoir"""
    enseignant = request.user
    
    if request.method == 'POST':
        form = DevoirForm(request.POST, request.FILES)
        if form.is_valid():
            devoir = form.save(commit=False)
            
            # Vérifier que le cours appartient à l'enseignant
            if devoir.cours.enseignant != enseignant:
                return HttpResponseForbidden("Action non autorisée")
            
            devoir.save()
            messages.success(request, f'Devoir "{devoir.titre}" ajouté avec succès!')
            return redirect('enseignants:mes_devoirs')
    else:
        form = DevoirForm()
        # Filtrer les cours pour n'afficher que ceux de l'enseignant
        # Utiliser try/except pour gérer le cas où le champ classe n'existe pas encore
        try:
            form.fields['cours'].queryset = Cours.objects.filter(enseignant=enseignant)
        except Exception:
            # Si le champ classe n'existe pas encore, utiliser only() pour spécifier les champs
            try:
                form.fields['cours'].queryset = Cours.objects.filter(enseignant=enseignant).only('id', 'titre', 'description', 'enseignant_id', 'created_at')
            except Exception:
                # Si only() ne fonctionne pas non plus, utiliser une requête basique
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute('SELECT id FROM cours_cours WHERE enseignant_id = %s', [enseignant.id])
                cours_ids = [row[0] for row in cursor.fetchall()]
                form.fields['cours'].queryset = Cours.objects.filter(id__in=cours_ids)
    
    return render(request, 'enseignant/ajouter_devoir.html', {'form': form})


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def supprimer_cours(request, cours_id):
    """Supprimer un cours"""
    enseignant = request.user
    cours = get_object_or_404(Cours, id=cours_id)
    
    if cours.enseignant != enseignant:
        return HttpResponseForbidden("Action non autorisée")
    
    titre = cours.titre
    cours.delete()
    messages.success(request, f'Cours "{titre}" supprimé avec succès!')
    
    return redirect('enseignants:mes_cours')


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def supprimer_devoir(request, devoir_id):
    """Supprimer un devoir"""
    enseignant = request.user
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if devoir.cours.enseignant != enseignant:
        return HttpResponseForbidden("Action non autorisée")
    
    titre = devoir.titre
    devoir.delete()
    messages.success(request, f'Devoir "{titre}" supprimé avec succès!')
    
    return redirect('mes_devoirs')


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def modifier_cours(request, cours_id):
    """Modifier un cours"""
    enseignant = request.user
    cours = get_object_or_404(Cours, id=cours_id, enseignant=enseignant)
    
    if request.method == 'POST':
        form = CoursForm(request.POST, request.FILES, instance=cours)
        if form.is_valid():
            # Vérifier que l'enseignant est assigné à la classe sélectionnée
            nouvelle_classe = form.cleaned_data['classe']
            if enseignant not in nouvelle_classe.enseignants.all():
                messages.error(request, "Vous n'êtes pas assigné à cette classe.")
                form.fields['classe'].queryset = enseignant.classes_enseignees.all()
                return render(request, 'enseignant/modifier_cours.html', {
                    'form': form,
                    'cours': cours
                })
            
            # Sauvegarder l'ancienne classe pour gérer les inscriptions
            ancienne_classe = cours.classe
            form.save()
            
            # Si la classe a changé, mettre à jour les inscriptions
            if ancienne_classe != nouvelle_classe:
                # Désinscrire les étudiants de l'ancienne classe
                if ancienne_classe:
                    etudiants_ancienne_classe = ancienne_classe.utilisateur_set.filter(role='etudiant')
                    Inscription.objects.filter(cours=cours, etudiant__in=etudiants_ancienne_classe).delete()
                
                # Inscrire les étudiants de la nouvelle classe
                if nouvelle_classe:
                    etudiants_nouvelle_classe = nouvelle_classe.utilisateur_set.filter(role='etudiant')
                    nb_inscrits = 0
                    for etudiant in etudiants_nouvelle_classe:
                        inscription, created = Inscription.objects.get_or_create(
                            cours=cours,
                            etudiant=etudiant
                        )
                        if created:
                            nb_inscrits += 1
                    
                    if nb_inscrits > 0:
                        messages.success(request, f'Cours "{cours.titre}" modifié avec succès! {nb_inscrits} étudiant(s) de la classe "{nouvelle_classe.nom}" inscrit(s) automatiquement.')
                    else:
                        messages.success(request, f'Cours "{cours.titre}" modifié avec succès!')
                else:
                    messages.success(request, f'Cours "{cours.titre}" modifié avec succès!')
            else:
                # Si la classe n'a pas changé, s'assurer que tous les étudiants de la classe sont inscrits
                if nouvelle_classe:
                    etudiants_classe = nouvelle_classe.utilisateur_set.filter(role='etudiant')
                    nb_inscrits = 0
                    for etudiant in etudiants_classe:
                        inscription, created = Inscription.objects.get_or_create(
                            cours=cours,
                            etudiant=etudiant
                        )
                        if created:
                            nb_inscrits += 1
                    
                    if nb_inscrits > 0:
                        messages.success(request, f'Cours "{cours.titre}" modifié avec succès! {nb_inscrits} étudiant(s) supplémentaire(s) inscrit(s).')
                    else:
                        messages.success(request, f'Cours "{cours.titre}" modifié avec succès!')
                else:
                    messages.success(request, f'Cours "{cours.titre}" modifié avec succès!')
            
                return redirect('enseignants:mes_cours')
    else:
        form = CoursForm(instance=cours)
        # Filtrer les classes pour n'afficher que celles où l'enseignant est assigné
        form.fields['classe'].queryset = enseignant.classes_enseignees.all()
    
    return render(request, 'enseignant/modifier_cours.html', {
        'form': form,
        'cours': cours
    })


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def modifier_devoir(request, devoir_id):
    """Modifier un devoir"""
    enseignant = request.user
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if devoir.cours.enseignant != enseignant:
        return HttpResponseForbidden("Action non autorisée")
    
    if request.method == 'POST':
        form = DevoirForm(request.POST, request.FILES, instance=devoir)
        if form.is_valid():
            # Vérifier que le cours appartient toujours à l'enseignant
            if form.cleaned_data['cours'].enseignant != enseignant:
                return HttpResponseForbidden("Action non autorisée")
            form.save()
            messages.success(request, f'Devoir "{devoir.titre}" modifié avec succès!')
            return redirect('enseignants:mes_devoirs')
    else:
        form = DevoirForm(instance=devoir)
        # Filtrer les cours pour n'afficher que ceux de l'enseignant
        # Utiliser try/except pour gérer le cas où le champ classe n'existe pas encore
        try:
            form.fields['cours'].queryset = Cours.objects.filter(enseignant=enseignant)
        except Exception:
            # Si le champ classe n'existe pas encore, utiliser only() pour spécifier les champs
            try:
                form.fields['cours'].queryset = Cours.objects.filter(enseignant=enseignant).only('id', 'titre', 'description', 'enseignant_id', 'created_at')
            except Exception:
                # Si only() ne fonctionne pas non plus, utiliser une requête basique
                from django.db import connection
                cursor = connection.cursor()
                cursor.execute('SELECT id FROM cours_cours WHERE enseignant_id = %s', [enseignant.id])
                cours_ids = [row[0] for row in cursor.fetchall()]
                form.fields['cours'].queryset = Cours.objects.filter(id__in=cours_ids)
    
    return render(request, 'enseignant/modifier_devoir.html', {
        'form': form,
        'devoir': devoir
    })


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def mes_classes(request):
    """Afficher les classes de l'enseignant"""
    enseignant = request.user
    
    # Récupérer toutes les classes où l'enseignant est assigné
    classes = enseignant.classes_enseignees.all().order_by('nom')
    
    # Pour chaque classe, récupérer le nombre d'étudiants et de cours
    classes_avec_stats = []
    for classe in classes:
        # Récupérer les étudiants de cette classe
        etudiants_classe = classe.utilisateur_set.filter(role='etudiant')
        # Récupérer les cours de l'enseignant pour cette classe
        # Utiliser try/except pour gérer le cas où le champ classe n'existe pas encore
        try:
            cours_classe = Cours.objects.filter(classe=classe, enseignant=enseignant)
            nb_cours = cours_classe.count()
        except Exception:
            # Si le champ classe n'existe pas encore, retourner 0
            nb_cours = 0
        
        classes_avec_stats.append({
            'classe': classe,
            'nb_etudiants': etudiants_classe.count(),
            'nb_cours': nb_cours,
        })
    
    context = {
        'enseignant': enseignant,
        'classes_avec_stats': classes_avec_stats,
        'total_classes': len(classes_avec_stats),
    }
    
    return render(request, 'enseignant/mes_classes.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def detail_classe(request, classe_id):
    """Afficher les détails d'une classe avec ses cours"""
    enseignant = request.user
    
    # Vérifier que l'enseignant est assigné à cette classe
    classe = get_object_or_404(Classe, id=classe_id)
    if enseignant not in classe.enseignants.all():
        messages.error(request, "Vous n'êtes pas assigné à cette classe.")
        return redirect('enseignants:mes_classes')
    
    # Récupérer les étudiants de cette classe
    etudiants_classe = classe.utilisateur_set.filter(role='etudiant')
    
    # Récupérer les cours de l'enseignant pour cette classe
    # Utiliser try/except pour gérer le cas où le champ classe n'existe pas encore
    try:
        cours_classe = Cours.objects.filter(classe=classe, enseignant=enseignant).order_by('-created_at')
    except Exception:
        # Si le champ classe n'existe pas encore, retourner une liste vide
        cours_classe = Cours.objects.none()
    
    # Pour chaque cours, compter les devoirs
    cours_avec_stats = []
    for cours in cours_classe:
        devoirs_cours = Devoir.objects.filter(cours=cours)
        cours_avec_stats.append({
            'cours': cours,
            'nb_devoirs': devoirs_cours.count(),
            'nb_etudiants_inscrits': Inscription.objects.filter(cours=cours, etudiant__in=etudiants_classe).count(),
        })
    
    context = {
        'classe': classe,
        'enseignant': enseignant,
        'nb_etudiants': etudiants_classe.count(),
        'cours_avec_stats': cours_avec_stats,
        'total_cours': len(cours_avec_stats),
    }
    
    return render(request, 'enseignant/detail_classe.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def detail_cours(request, cours_id):
    """Afficher les détails d'un cours avec ses devoirs"""
    enseignant = request.user
    
    # Vérifier que le cours appartient à l'enseignant
    cours = get_object_or_404(Cours, id=cours_id, enseignant=enseignant)
    
    # Récupérer les devoirs de ce cours
    devoirs = Devoir.objects.filter(cours=cours).order_by('deadline')
    
    # Pour chaque devoir, compter les soumissions
    now = timezone.now()
    devoirs_avec_stats = []
    for devoir in devoirs:
        soumissions = Soumission.objects.filter(devoir=devoir)
        devoirs_avec_stats.append({
            'devoir': devoir,
            'nb_soumissions': soumissions.count(),
            'est_en_retard': devoir.deadline < now,
        })
    
    # Récupérer les étudiants inscrits à ce cours
    inscriptions = Inscription.objects.filter(cours=cours)
    etudiants_inscrits = [inscription.etudiant for inscription in inscriptions]
    
    context = {
        'cours': cours,
        'enseignant': enseignant,
        'devoirs_avec_stats': devoirs_avec_stats,
        'total_devoirs': len(devoirs_avec_stats),
        'etudiants_inscrits': etudiants_inscrits,
        'nb_etudiants_inscrits': len(etudiants_inscrits),
        'now': now,
    }
    
    return render(request, 'enseignant/detail_cours.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def mes_cours(request):
    """Afficher tous les cours de l'enseignant"""
    enseignant = request.user
    
    # Récupérer tous les cours de l'enseignant
    try:
        cours = Cours.objects.filter(enseignant=enseignant).order_by('-created_at')
    except Exception:
        try:
            cours = Cours.objects.filter(enseignant=enseignant).only('id', 'titre', 'description', 'enseignant_id', 'created_at').order_by('-created_at')
        except Exception:
            cours = Cours.objects.none()
    
    # Pour chaque cours, récupérer les statistiques
    cours_avec_stats = []
    for c in cours:
        try:
            nb_inscriptions = Inscription.objects.filter(cours=c).count()
            nb_devoirs = Devoir.objects.filter(cours=c).count()
        except Exception:
            nb_inscriptions = 0
            nb_devoirs = 0
        
        cours_avec_stats.append({
            'cours': c,
            'nb_inscriptions': nb_inscriptions,
            'nb_devoirs': nb_devoirs,
        })
    
    context = {
        'enseignant': enseignant,
        'cours_avec_stats': cours_avec_stats,
        'total_cours': len(cours_avec_stats),
    }
    
    return render(request, 'enseignant/mes_cours.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def mes_devoirs(request):
    """Afficher tous les devoirs de l'enseignant"""
    enseignant = request.user
    
    # Récupérer tous les devoirs de l'enseignant
    devoirs = Devoir.objects.filter(cours__enseignant=enseignant).order_by('-created_at')
    
    # Pour chaque devoir, récupérer les statistiques
    now = timezone.now()
    devoirs_avec_stats = []
    for devoir in devoirs:
        try:
            nb_soumissions = Soumission.objects.filter(devoir=devoir).count()
            est_en_retard = now > devoir.deadline
        except Exception:
            nb_soumissions = 0
            est_en_retard = False
        
        devoirs_avec_stats.append({
            'devoir': devoir,
            'nb_soumissions': nb_soumissions,
            'est_en_retard': est_en_retard,
        })
    
    context = {
        'enseignant': enseignant,
        'devoirs_avec_stats': devoirs_avec_stats,
        'total_devoirs': len(devoirs_avec_stats),
        'now': now,
    }
    
    return render(request, 'enseignant/mes_devoirs.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def etudiants_classe(request, classe_id):
    """Afficher les étudiants d'une classe avec leurs notes"""
    enseignant = request.user
    
    # Vérifier que l'enseignant est assigné à cette classe
    classe = get_object_or_404(Classe, id=classe_id)
    if enseignant not in classe.enseignants.all():
        messages.error(request, "Vous n'êtes pas assigné à cette classe.")
        return redirect('enseignants:mes_classes')
    
    # Récupérer les étudiants de cette classe
    etudiants = classe.utilisateur_set.filter(role='etudiant').order_by('username')
    
    # Pour chaque étudiant, récupérer ses notes attribuées par cet enseignant
    etudiants_avec_notes = []
    for etudiant in etudiants:
        notes_etudiant = Note.objects.filter(etudiant=etudiant, enseignant=enseignant).order_by('-date_attribution')
        moyenne = notes_etudiant.aggregate(Avg('note'))['note__avg']
        etudiants_avec_notes.append({
            'etudiant': etudiant,
            'notes': notes_etudiant,
            'nb_notes': notes_etudiant.count(),
            'moyenne': round(moyenne, 2) if moyenne else None,
        })
    
    context = {
        'classe': classe,
        'enseignant': enseignant,
        'etudiants_avec_notes': etudiants_avec_notes,
        'total_etudiants': len(etudiants_avec_notes),
    }
    
    return render(request, 'enseignant/etudiants_classe.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def ajouter_note(request, classe_id, etudiant_id=None):
    """Ajouter une note à un étudiant"""
    enseignant = request.user
    
    # Vérifier que l'enseignant est assigné à cette classe
    classe = get_object_or_404(Classe, id=classe_id)
    if enseignant not in classe.enseignants.all():
        messages.error(request, "Vous n'êtes pas assigné à cette classe.")
        return redirect('enseignants:mes_classes')
    
    # Si un étudiant est spécifié, le récupérer
    etudiant = None
    if etudiant_id:
        etudiant = get_object_or_404(Utilisateur, id=etudiant_id, role='etudiant', classe=classe)
    
    if request.method == 'POST':
        form = NoteForm(request.POST, enseignant=enseignant, classe=classe)
        if form.is_valid():
            note = form.save(commit=False)
            note.enseignant = enseignant
            note.save()
            messages.success(request, f'Note {note.note}/20 attribuée à {note.etudiant.username} avec succès!')
            return redirect('enseignants:etudiants_classe', classe_id=classe.id)
    else:
        form = NoteForm(enseignant=enseignant, classe=classe)
        if etudiant:
            form.fields['etudiant'].initial = etudiant
    
    context = {
        'form': form,
        'classe': classe,
        'etudiant': etudiant,
    }
    
    return render(request, 'enseignant/ajouter_note.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def modifier_note(request, note_id):
    """Modifier une note"""
    enseignant = request.user
    note = get_object_or_404(Note, id=note_id, enseignant=enseignant)
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note, enseignant=enseignant, classe=note.etudiant.classe)
        if form.is_valid():
            form.save()
            messages.success(request, f'Note modifiée avec succès!')
            return redirect('enseignants:etudiants_classe', classe_id=note.etudiant.classe.id)
    else:
        form = NoteForm(instance=note, enseignant=enseignant, classe=note.etudiant.classe)
    
    context = {
        'form': form,
        'note': note,
        'classe': note.etudiant.classe,
    }
    
    return render(request, 'enseignant/modifier_note.html', context)


@login_required
@user_passes_test(is_enseignant, login_url='/enseignant/login/')
def supprimer_note(request, note_id):
    """Supprimer une note"""
    enseignant = request.user
    note = get_object_or_404(Note, id=note_id, enseignant=enseignant)
    classe_id = note.etudiant.classe.id
    
    if request.method == 'POST':
        etudiant_username = note.etudiant.username
        note.delete()
        messages.success(request, f'Note supprimée avec succès!')
        return redirect('enseignants:etudiants_classe', classe_id=classe_id)
    
    context = {
        'note': note,
        'classe': note.etudiant.classe,
    }
    
    return render(request, 'enseignant/supprimer_note.html', context)

