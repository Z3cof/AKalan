from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, F
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Utilisateur, Classe, Invitation
from cours.models import Cours, Inscription
from devoirs.models import Devoir, Soumission

#----------------------------------Gestion des permissions----------------------------------
def is_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.role == 'admin'

#----------------------------------Gestion de la page d'accueil----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_dashboard(request):
    """Dashboard principal de l'administrateur"""
    # Statistiques
    total_etudiants = Utilisateur.objects.filter(role='etudiant').count()
    total_enseignants = Utilisateur.objects.filter(role='enseignant').count()
    total_cours = Cours.objects.count()
    total_devoirs = Devoir.objects.count()
    total_inscriptions = Inscription.objects.count()
    total_soumissions = Soumission.objects.count()
    
    # Statistiques des soumissions
    now = timezone.now()
    soumissions_a_temps = Soumission.objects.filter(date_soumission__lte=F('devoir__deadline')).count()
    soumissions_en_retard = Soumission.objects.filter(date_soumission__gt=F('devoir__deadline')).count()
    
    # Cours récents
    cours_recents = Cours.objects.select_related('enseignant').order_by('-created_at')[:5]
    
    # Devoirs récents
    devoirs_recents = Devoir.objects.select_related('cours', 'cours__enseignant').order_by('-created_at')[:5]
    
    # Utilisateurs récents
    utilisateurs_recents = Utilisateur.objects.order_by('-date_joined')[:5]
    
    context = {
        'total_etudiants': total_etudiants,
        'total_enseignants': total_enseignants,
        'total_cours': total_cours,
        'total_devoirs': total_devoirs,
        'total_inscriptions': total_inscriptions,
        'total_soumissions': total_soumissions,
        'soumissions_a_temps': soumissions_a_temps,
        'soumissions_en_retard': soumissions_en_retard,
        'cours_recents': cours_recents,
        'devoirs_recents': devoirs_recents,
        'utilisateurs_recents': utilisateurs_recents,
    }
    return render(request, 'admin/dashboard.html', context)

#----------------------------------Gestion de la page des utilisateurs----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_utilisateurs(request):
    """Gestion des utilisateurs"""
    role_filter = request.GET.get('role', '')
    search_query = request.GET.get('search', '')
    
    utilisateurs = Utilisateur.objects.all()
    
    if role_filter:
        utilisateurs = utilisateurs.filter(role=role_filter)
    
    if search_query:
        utilisateurs = utilisateurs.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Statistiques par rôle
    stats = {
        'total': utilisateurs.count(),
        'admin': Utilisateur.objects.filter(role='admin').count(),
        'enseignant': Utilisateur.objects.filter(role='enseignant').count(),
        'etudiant': Utilisateur.objects.filter(role='etudiant').count(),
    }
    
    context = {
        'utilisateurs': utilisateurs,
        'stats': stats,
        'role_filter': role_filter,
        'search_query': search_query,
    }
    return render(request, 'admin/utilisateurs.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_cours(request):
    """Gestion des cours"""
    search_query = request.GET.get('search', '')
    
    cours = Cours.objects.select_related('enseignant').annotate(
        nb_inscriptions=Count('inscription')
    ).order_by('-created_at')
    
    if search_query:
        cours = cours.filter(
            Q(titre__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(enseignant__username__icontains=search_query)
        )
    
    context = {
        'cours': cours,
        'search_query': search_query,
    }
    return render(request, 'admin/cours.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_devoirs(request):
    """Gestion des devoirs"""
    search_query = request.GET.get('search', '')
    
    devoirs = Devoir.objects.select_related('cours', 'cours__enseignant').annotate(
        nb_soumissions=Count('soumission')
    ).order_by('-created_at')
    
    if search_query:
        devoirs = devoirs.filter(
            Q(titre__icontains=search_query) |
            Q(cours__titre__icontains=search_query)
        )
    
    now = timezone.now()
    context = {
        'devoirs': devoirs,
        'search_query': search_query,
        'now': now,
    }
    return render(request, 'admin/devoirs.html', context)


#----------------------------------Gestion de la page d'accueil----------------------------------
def home(request):
    """Page d'accueil - redirige vers le dashboard selon le rôle"""
    if request.user.is_authenticated:
        if request.user.role == 'admin':
            return redirect('admin_dashboard')
        elif request.user.role == 'enseignant':
            return redirect('enseignants:dashboard_enseignant')
        elif request.user.role == 'etudiant':
            return redirect('etudiants:dashboard_etudiant')
    
    # Si l'utilisateur n'est pas authentifié, vérifier s'il y a un paramètre 'next' dans l'URL
    # pour déterminer vers quel login rediriger
    next_url = request.GET.get('next', '')
    if '/enseignant/' in next_url:
        return redirect('/enseignant/login/?next=' + next_url)
    elif '/etudiant/' in next_url:
        return redirect('/etudiant/login/?next=' + next_url)
    else:
        return redirect('admin_login')

#----------------------------------Gestion de la connexion----------------------------------
def admin_login(request):
    """Page de connexion pour l'administrateur"""
    if request.user.is_authenticated and request.user.role == 'admin':
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = Utilisateur.objects.get(username=username)
            if user.check_password(password) and user.role == 'admin':
                login(request, user)
                messages.success(request, f'Bienvenue, {user.username}!')
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Identifiants incorrects ou vous n\'êtes pas administrateur.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Identifiants incorrects.')
    
    return render(request, 'admin/login.html')

#----------------------------------Gestion de la deconnexion----------------------------------
@login_required
def admin_logout(request):
    """Déconnexion - redirige vers le login approprié selon le rôle"""
    role = request.user.role
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    if role == 'enseignant':
        return redirect('enseignants:enseignant_login')
    elif role == 'etudiant':
        return redirect('etudiants:etudiant_login')
    return redirect('admin_login')

#----------------------------------Gestion des invitations enseignant----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_inviter_enseignant(request):
    """Inviter un nouvel enseignant par email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Validation
        if not email:
            messages.error(request, 'L\'email est obligatoire.')
            return render(request, 'admin/inviter_enseignant.html')
        
        # Vérifier si l'utilisateur existe déjà
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
            return render(request, 'admin/inviter_enseignant.html')
        
        # Vérifier si une invitation en attente existe déjà
        if Invitation.objects.filter(email=email, role='enseignant', statut='en_attente').exists():
            messages.warning(request, 'Une invitation a déjà été envoyée à cet email.')
            return render(request, 'admin/inviter_enseignant.html')
        
        # Créer l'invitation
        try:
            invitation = Invitation.objects.create(
                email=email,
                role='enseignant',
                cree_par=request.user
            )
            
            # Envoyer l'email d'invitation
            lien_invitation = f"{settings.SITE_URL}/admin/accepter-invitation/{invitation.token}/"
            sujet = "Invitation à rejoindre AKalan en tant qu'enseignant"
            message_html = render_to_string('admin/email_invitation.html', {
                'invitation': invitation,
                'lien': lien_invitation,
                'role': 'enseignant'
            })
            
            send_mail(
                sujet,
                f"Vous avez été invité à rejoindre AKalan en tant qu'enseignant. Cliquez sur ce lien pour créer votre compte: {lien_invitation}",
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@akalan.com',
                [email],
                html_message=message_html,
                fail_silently=False,
            )
            
            messages.success(request, f'Invitation envoyée avec succès à {email}!')
            return redirect('admin_utilisateurs')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'envoi de l\'invitation: {str(e)}')
    
    return render(request, 'admin/inviter_enseignant.html')

#----------------------------------Gestion des invitations etudiant----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_inviter_etudiant(request):
    """Inviter un nouvel étudiant par email"""
    classes = Classe.objects.all().order_by('nom')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        classe_id = request.POST.get('classe', '')
        
        # Validation
        if not email:
            messages.error(request, 'L\'email est obligatoire.')
            return render(request, 'admin/inviter_etudiant.html', {'classes': classes})
        
        # Vérifier si l'utilisateur existe déjà
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
            return render(request, 'admin/inviter_etudiant.html', {'classes': classes})
        
        # Vérifier si une invitation en attente existe déjà
        if Invitation.objects.filter(email=email, role='etudiant', statut='en_attente').exists():
            messages.warning(request, 'Une invitation a déjà été envoyée à cet email.')
            return render(request, 'admin/inviter_etudiant.html', {'classes': classes})
        
        # Créer l'invitation
        try:
            classe = None
            if classe_id:
                try:
                    classe = Classe.objects.get(id=classe_id)
                except Classe.DoesNotExist:
                    messages.warning(request, 'La classe sélectionnée n\'existe plus.')
            
            invitation = Invitation.objects.create(
                email=email,
                role='etudiant',
                classe=classe,
                cree_par=request.user
            )
            
            # Envoyer l'email d'invitation
            lien_invitation = f"{settings.SITE_URL}/admin/accepter-invitation/{invitation.token}/"
            sujet = "Invitation à rejoindre AKalan en tant qu'étudiant"
            message_html = render_to_string('admin/email_invitation.html', {
                'invitation': invitation,
                'lien': lien_invitation,
                'role': 'étudiant'
            })
            
            send_mail(
                sujet,
                f"Vous avez été invité à rejoindre AKalan en tant qu'étudiant. Cliquez sur ce lien pour créer votre compte: {lien_invitation}",
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@akalan.com',
                [email],
                html_message=message_html,
                fail_silently=False,
            )
            
            messages.success(request, f'Invitation envoyée avec succès à {email}!')
            # Rediriger vers la page de la classe si une classe a été assignée
            if classe:
                return redirect('admin_detail_classe', classe_id=classe.id)
            return redirect('admin_utilisateurs')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue lors de l\'envoi de l\'invitation: {str(e)}')
    
    return render(request, 'admin/inviter_etudiant.html', {'classes': classes})


#----------------------------------Gestion de l'acceptation d'invitation----------------------------------
def accepter_invitation(request, token):
    """Permet à un utilisateur d'accepter une invitation et de créer son compte"""
    invitation = get_object_or_404(Invitation, token=token)
    
    # Vérifier si l'invitation est valide
    if invitation.est_expiree():
        invitation.statut = 'expiree'
        invitation.save()
        messages.error(request, 'Cette invitation a expiré. Veuillez contacter l\'administrateur.')
        return render(request, 'admin/invitation_expiree.html', {'invitation': invitation})
    
    if invitation.statut != 'en_attente':
        messages.error(request, 'Cette invitation a déjà été utilisée.')
        return render(request, 'admin/invitation_expiree.html', {'invitation': invitation})
    
    # Vérifier si l'utilisateur existe déjà
    if Utilisateur.objects.filter(email=invitation.email).exists():
        messages.error(request, 'Un compte avec cet email existe déjà.')
        invitation.statut = 'expiree'
        invitation.save()
        return render(request, 'admin/invitation_expiree.html', {'invitation': invitation})
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Validation
        if not username or not password or not password_confirm:
            messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
            return render(request, 'admin/accepter_invitation.html', {'invitation': invitation})
        
        if password != password_confirm:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'admin/accepter_invitation.html', {'invitation': invitation})
        
        if Utilisateur.objects.filter(username=username).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            return render(request, 'admin/accepter_invitation.html', {'invitation': invitation})
        
        # Créer l'utilisateur
        try:
            utilisateur = Utilisateur.objects.create_user(
                username=username,
                email=invitation.email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=invitation.role,
                classe=invitation.classe
            )
            
            # Marquer l'invitation comme acceptée
            invitation.accepter()
            
            messages.success(request, f'Compte créé avec succès! Vous pouvez maintenant vous connecter.')
            
            # Rediriger vers la page de connexion appropriée
            if invitation.role == 'enseignant':
                return redirect('enseignants:enseignant_login')
            elif invitation.role == 'etudiant':
                return redirect('etudiants:etudiant_login')
            else:
                return redirect('admin_login')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/accepter_invitation.html', {'invitation': invitation})

#----------------------------------Gestion des classes----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_classes(request):
    """Gestion des classes"""
    search_query = request.GET.get('search', '')
    
    classes = Classe.objects.prefetch_related('enseignants').annotate(
        nb_etudiants=Count('utilisateur', filter=Q(utilisateur__role='etudiant'))
    ).order_by('nom')
    
    if search_query:
        classes = classes.filter(
            Q(nom__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(enseignants__username__icontains=search_query)
        )
    
    context = {
        'classes': classes,
        'search_query': search_query,
    }
    return render(request, 'admin/classes.html', context)

#----------------------------------Gestion des ajouts classe----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_ajouter_classe(request):
    """Ajouter une nouvelle classe"""
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description', '')
        
        # Validation
        if not nom:
            messages.error(request, 'Le nom de la classe est obligatoire.')
            return render(request, 'admin/ajouter_classe.html')
        
        # Vérifier si la classe existe déjà
        if Classe.objects.filter(nom=nom).exists():
            messages.error(request, 'Une classe avec ce nom existe déjà.')
            return render(request, 'admin/ajouter_classe.html')
        
        # Créer la classe
        try:
            classe = Classe.objects.create(
                nom=nom,
                description=description
            )
            messages.success(request, f'Classe "{classe.nom}" créée avec succès!')
            return redirect('admin_classes')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/ajouter_classe.html')


#----------------------------------Gestion de l'assignation d'enseignant à une classe----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_assigner_enseignant(request):
    """Assigner un ou plusieurs enseignants à une classe"""
    classes = Classe.objects.all().order_by('nom')
    enseignants = Utilisateur.objects.filter(role='enseignant')
    
    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        enseignant_ids = request.POST.getlist('enseignants')  # Récupérer plusieurs enseignants
        
        # Validation
        if not classe_id:
            messages.error(request, 'Veuillez sélectionner une classe.')
            return render(request, 'admin/assigner_enseignant.html', {'classes': classes, 'enseignants': enseignants})
        
        if not enseignant_ids:
            messages.error(request, 'Veuillez sélectionner au moins un enseignant.')
            return render(request, 'admin/assigner_enseignant.html', {'classes': classes, 'enseignants': enseignants})
        
        try:
            classe = Classe.objects.get(id=classe_id)
            enseignants_assignes = []
            enseignants_deja_assignes = []
            
            for enseignant_id in enseignant_ids:
                enseignant = Utilisateur.objects.get(id=enseignant_id, role='enseignant')
                
                # Vérifier si l'enseignant est déjà dans cette classe
                if classe.enseignants.filter(id=enseignant.id).exists():
                    enseignants_deja_assignes.append(enseignant.username)
                else:
                    classe.enseignants.add(enseignant)
                    enseignants_assignes.append(enseignant.username)
            
            if enseignants_assignes:
                messages.success(request, f'Enseignant(s) "{", ".join(enseignants_assignes)}" assigné(s) à la classe "{classe.nom}" avec succès!')
            
            if enseignants_deja_assignes:
                messages.warning(request, f'Enseignant(s) "{", ".join(enseignants_deja_assignes)}" déjà assigné(s) à cette classe.')
                
        except Classe.DoesNotExist:
            messages.error(request, 'La classe sélectionnée n\'existe pas.')
        except Utilisateur.DoesNotExist:
            messages.error(request, 'Un enseignant sélectionné n\'existe pas.')
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/assigner_enseignant.html', {'classes': classes, 'enseignants': enseignants})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_retirer_enseignant(request, classe_id, enseignant_id):
    """Retirer un enseignant d'une classe"""
    classe = get_object_or_404(Classe, id=classe_id)
    enseignant = get_object_or_404(Utilisateur, id=enseignant_id, role='enseignant')
    
    if request.method == 'POST':
        if classe.enseignants.filter(id=enseignant.id).exists():
            classe.enseignants.remove(enseignant)
            messages.success(request, f'Enseignant "{enseignant.username}" retiré de la classe "{classe.nom}" avec succès!')
        else:
            messages.warning(request, f'L\'enseignant "{enseignant.username}" n\'est pas assigné à cette classe.')
        
        return redirect('admin_detail_classe', classe_id=classe.id)
    
    # Afficher une page de confirmation
    context = {
        'classe': classe,
        'enseignant': enseignant,
    }
    return render(request, 'admin/retirer_enseignant.html', context)


#----------------------------------Gestion des détails----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_detail_utilisateur(request, utilisateur_id):
    """Détails d'un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    
    context = {
        'utilisateur': utilisateur,
    }
    
    # Ajouter des statistiques selon le rôle
    if utilisateur.role == 'etudiant':
        context['nb_inscriptions'] = Inscription.objects.filter(etudiant=utilisateur).count()
        context['nb_soumissions'] = Soumission.objects.filter(etudiant=utilisateur).count()
    elif utilisateur.role == 'enseignant':
        context['nb_cours'] = Cours.objects.filter(enseignant=utilisateur).count()
        context['nb_classes'] = Classe.objects.filter(enseignants=utilisateur).count()
    
    return render(request, 'admin/detail_utilisateur.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_detail_classe(request, classe_id):
    """Détails d'une classe"""
    classe = get_object_or_404(Classe.objects.prefetch_related('enseignants'), id=classe_id)
    etudiants = Utilisateur.objects.filter(classe=classe, role='etudiant').order_by('last_name', 'first_name')
    
    # Récupérer tous les enseignants assignés à cette classe
    enseignants = classe.enseignants.all()
    
    context = {
        'classe': classe,
        'etudiants': etudiants,
        'nb_etudiants': etudiants.count(),
        'enseignants': enseignants,
    }
    
    return render(request, 'admin/detail_classe.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_detail_cours(request, cours_id):
    """Détails d'un cours"""
    cours = get_object_or_404(Cours, id=cours_id)
    inscriptions = Inscription.objects.filter(cours=cours).select_related('etudiant')
    devoirs = Devoir.objects.filter(cours=cours).annotate(
        nb_soumissions=Count('soumission')
    ).order_by('-created_at')
    
    context = {
        'cours': cours,
        'inscriptions': inscriptions,
        'devoirs': devoirs,
        'nb_inscriptions': inscriptions.count(),
        'nb_devoirs': devoirs.count(),
    }
    
    return render(request, 'admin/detail_cours.html', context)


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_detail_devoir(request, devoir_id):
    """Détails d'un devoir"""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    soumissions = Soumission.objects.filter(devoir=devoir).select_related('etudiant').order_by('-date_soumission')
    now = timezone.now()
    
    context = {
        'devoir': devoir,
        'soumissions': soumissions,
        'nb_soumissions': soumissions.count(),
        'now': now,
    }
    
    return render(request, 'admin/detail_devoir.html', context)


#----------------------------------Gestion des modifications (CRUD)----------------------------------
@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_modifier_utilisateur(request, utilisateur_id):
    """Modifier un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    classes = Classe.objects.all().order_by('nom')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        classe_id = request.POST.get('classe', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Vérifier si le username existe déjà (sauf pour l'utilisateur actuel)
        if Utilisateur.objects.filter(username=username).exclude(id=utilisateur_id).exists():
            messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            return render(request, 'admin/modifier_utilisateur.html', {'utilisateur': utilisateur, 'classes': classes})
        
        # Vérifier si l'email existe déjà (sauf pour l'utilisateur actuel)
        if email and Utilisateur.objects.filter(email=email).exclude(id=utilisateur_id).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
            return render(request, 'admin/modifier_utilisateur.html', {'utilisateur': utilisateur, 'classes': classes})
        
        try:
            utilisateur.username = username
            utilisateur.email = email
            utilisateur.first_name = first_name
            utilisateur.last_name = last_name
            utilisateur.is_active = is_active
            
            if classe_id and utilisateur.role == 'etudiant':
                classe = Classe.objects.get(id=classe_id)
                utilisateur.classe = classe
            elif not classe_id and utilisateur.role == 'etudiant':
                utilisateur.classe = None
            
            utilisateur.save()
            messages.success(request, f'Utilisateur "{utilisateur.username}" modifié avec succès!')
            return redirect('admin_detail_utilisateur', utilisateur_id=utilisateur.id)
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/modifier_utilisateur.html', {'utilisateur': utilisateur, 'classes': classes})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_supprimer_utilisateur(request, utilisateur_id):
    """Supprimer un utilisateur"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    
    if request.method == 'POST':
        username = utilisateur.username
        utilisateur.delete()
        messages.success(request, f'Utilisateur "{username}" supprimé avec succès!')
        return redirect('admin_utilisateurs')
    
    return render(request, 'admin/supprimer_utilisateur.html', {'utilisateur': utilisateur})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_modifier_classe(request, classe_id):
    """Modifier une classe"""
    classe = get_object_or_404(Classe, id=classe_id)
    enseignants = Utilisateur.objects.filter(role='enseignant')
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        description = request.POST.get('description', '')
        enseignant_id = request.POST.get('enseignant', '')
        
        if not nom:
            messages.error(request, 'Le nom de la classe est obligatoire.')
            return render(request, 'admin/modifier_classe.html', {'classe': classe, 'enseignants': enseignants})
        
        # Vérifier si le nom existe déjà (sauf pour la classe actuelle)
        if Classe.objects.filter(nom=nom).exclude(id=classe_id).exists():
            messages.error(request, 'Une classe avec ce nom existe déjà.')
            return render(request, 'admin/modifier_classe.html', {'classe': classe, 'enseignants': enseignants})
        
        try:
            classe.nom = nom
            classe.description = description
            
            # Gérer les enseignants (ManyToMany)
            enseignant_ids = request.POST.getlist('enseignants')
            if enseignant_ids:
                enseignants = Utilisateur.objects.filter(id__in=enseignant_ids, role='enseignant')
                classe.enseignants.set(enseignants)
            else:
                classe.enseignants.clear()
            
            classe.save()
            messages.success(request, f'Classe "{classe.nom}" modifiée avec succès!')
            return redirect('admin_detail_classe', classe_id=classe.id)
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/modifier_classe.html', {'classe': classe, 'enseignants': enseignants})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_supprimer_classe(request, classe_id):
    """Supprimer une classe"""
    classe = get_object_or_404(Classe, id=classe_id)
    
    if request.method == 'POST':
        nom = classe.nom
        classe.delete()
        messages.success(request, f'Classe "{nom}" supprimée avec succès!')
        return redirect('admin_classes')
    
    return render(request, 'admin/supprimer_classe.html', {'classe': classe})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_modifier_cours(request, cours_id):
    """Modifier un cours"""
    cours = get_object_or_404(Cours, id=cours_id)
    enseignants = Utilisateur.objects.filter(role='enseignant')
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description', '')
        enseignant_id = request.POST.get('enseignant')
        
        if not titre or not enseignant_id:
            messages.error(request, 'Le titre et l\'enseignant sont obligatoires.')
            return render(request, 'admin/modifier_cours.html', {'cours': cours, 'enseignants': enseignants})
        
        try:
            cours.titre = titre
            cours.description = description
            cours.enseignant = Utilisateur.objects.get(id=enseignant_id, role='enseignant')
            cours.save()
            messages.success(request, f'Cours "{cours.titre}" modifié avec succès!')
            return redirect('admin_detail_cours', cours_id=cours.id)
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/modifier_cours.html', {'cours': cours, 'enseignants': enseignants})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_supprimer_cours(request, cours_id):
    """Supprimer un cours"""
    cours = get_object_or_404(Cours, id=cours_id)
    
    if request.method == 'POST':
        titre = cours.titre
        cours.delete()
        messages.success(request, f'Cours "{titre}" supprimé avec succès!')
        return redirect('admin_cours')
    
    return render(request, 'admin/supprimer_cours.html', {'cours': cours})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_modifier_devoir(request, devoir_id):
    """Modifier un devoir"""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    cours_list = Cours.objects.all()
    
    if request.method == 'POST':
        titre = request.POST.get('titre')
        description = request.POST.get('description', '')
        cours_id = request.POST.get('cours')
        deadline = request.POST.get('deadline')
        
        if not titre or not cours_id or not deadline:
            messages.error(request, 'Le titre, le cours et la deadline sont obligatoires.')
            return render(request, 'admin/modifier_devoir.html', {'devoir': devoir, 'cours_list': cours_list})
        
        try:
            from django.utils.dateparse import parse_datetime
            devoir.titre = titre
            devoir.description = description
            devoir.cours = Cours.objects.get(id=cours_id)
            devoir.deadline = parse_datetime(deadline)
            devoir.save()
            messages.success(request, f'Devoir "{devoir.titre}" modifié avec succès!')
            return redirect('admin_detail_devoir', devoir_id=devoir.id)
        except Exception as e:
            messages.error(request, f'Une erreur est survenue: {str(e)}')
    
    return render(request, 'admin/modifier_devoir.html', {'devoir': devoir, 'cours_list': cours_list})


@login_required
@user_passes_test(is_admin, login_url='/admin/login/')
def admin_supprimer_devoir(request, devoir_id):
    """Supprimer un devoir"""
    devoir = get_object_or_404(Devoir, id=devoir_id)
    
    if request.method == 'POST':
        titre = devoir.titre
        devoir.delete()
        messages.success(request, f'Devoir "{titre}" supprimé avec succès!')
        return redirect('admin_devoirs')
    
    return render(request, 'admin/supprimer_devoir.html', {'devoir': devoir})

#gerer la decoonexion automatique apres inactivité de 15 minutes
@login_required
def deconnexion_automatique(request):
    """Déconnexion automatique après inactivité de 15 minutes"""
    if request.user.is_authenticated:
        request.session.modified = True
        request.session.set_expiry(900)
    return redirect('admin_login')
    return redirect('enseignants:enseignant_login')
    return redirect('etudiants:etudiant_login')
    return redirect('enseignant:enseignant_login')

    