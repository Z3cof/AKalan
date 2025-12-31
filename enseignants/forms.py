from django import forms
from cours.models import Cours
from devoirs.models import Devoir
from comptes.models import Classe, Note
from django.utils import timezone


class CoursForm(forms.ModelForm):
    class Meta:
        model = Cours
        fields = ['titre', 'description', 'classe', 'fichier_pdf']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white',
                'placeholder': 'Titre du cours'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white',
                'rows': 6,
                'placeholder': 'Description du cours'
            }),
            'classe': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white'
            }),
            'fichier_pdf': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-green-600 file:text-white hover:file:bg-green-700 file:cursor-pointer',
                'accept': '.pdf'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre le champ classe obligatoire dans le formulaire
        self.fields['classe'].required = True


class DevoirForm(forms.ModelForm):
    class Meta:
        model = Devoir
        fields = ['titre', 'description', 'deadline', 'cours', 'fichier']
        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-300 text-white',
                'placeholder': 'Titre du devoir'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-300 text-white',
                'rows': 6,
                'placeholder': 'Description du devoir'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-300 text-white'
            }),
            'cours': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-300 text-white'
            }),
            'fichier': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all duration-300 text-white'
            }),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['etudiant', 'devoir', 'note', 'commentaire']
        widgets = {
            'etudiant': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white'
            }),
            'devoir': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white'
            }),
            'note': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white',
                'step': '0.01',
                'min': '0',
                'max': '20',
                'placeholder': 'Note sur 20'
            }),
            'commentaire': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all duration-300 text-white',
                'rows': 4,
                'placeholder': 'Commentaire (optionnel)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        enseignant = kwargs.pop('enseignant', None)
        classe = kwargs.pop('classe', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les étudiants par classe si une classe est fournie
        if classe:
            self.fields['etudiant'].queryset = classe.utilisateur_set.filter(role='etudiant').order_by('username')
        else:
            # Si pas de classe spécifiée, n'afficher aucun étudiant par défaut
            self.fields['etudiant'].queryset = Utilisateur.objects.none()
        
        # Filtrer les devoirs par enseignant et classe
        if enseignant:
            try:
                if classe:
                    # Filtrer les devoirs des cours de l'enseignant pour cette classe
                    cours_classe = Cours.objects.filter(enseignant=enseignant, classe=classe)
                    self.fields['devoir'].queryset = Devoir.objects.filter(cours__in=cours_classe).order_by('titre')
                else:
                    # Si pas de classe, afficher tous les devoirs de l'enseignant
                    self.fields['devoir'].queryset = Devoir.objects.filter(cours__enseignant=enseignant).order_by('titre')
            except Exception:
                self.fields['devoir'].queryset = Devoir.objects.none()
        else:
            self.fields['devoir'].queryset = Devoir.objects.none()
        
        # Rendre le devoir obligatoire
        self.fields['devoir'].required = True
