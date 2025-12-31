# Configuration de l'envoi d'emails

## Configuration pour Gmail

Pour envoyer de vrais emails avec Gmail, suivez ces étapes :

### 1. Activer l'authentification à deux facteurs
- Allez sur https://myaccount.google.com/security
- Activez la "Validation en deux étapes" si ce n'est pas déjà fait

### 2. Créer un mot de passe d'application
- Allez sur https://myaccount.google.com/apppasswords
- Sélectionnez "Sélectionner une app" → "Autre (nom personnalisé)"
- Entrez "AKalan" comme nom
- Cliquez sur "Générer"
- **Copiez le mot de passe de 16 caractères** (sans espaces)

### 3. Configurer dans settings.py
Ouvrez `AKalan/settings.py` et modifiez :

```python
EMAIL_HOST_USER = 'votre_email@gmail.com'  # Votre adresse Gmail
EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'  # Le mot de passe d'application (16 caractères)
```

### 4. Tester l'envoi
Après avoir configuré, testez en invitant un utilisateur depuis l'interface admin.

## Configuration pour d'autres fournisseurs

### Outlook/Hotmail
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre_email@outlook.com'
EMAIL_HOST_PASSWORD = 'votre_mot_de_passe'
```

### Yahoo
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'votre_email@yahoo.com'
EMAIL_HOST_PASSWORD = 'votre_mot_de_passe'
```

### Autres fournisseurs
Consultez la documentation de votre fournisseur pour les paramètres SMTP.

## Sécurité (Recommandé pour la production)

Pour plus de sécurité, utilisez des variables d'environnement au lieu de mettre les mots de passe directement dans le code :

1. Installez `python-decouple` :
```bash
pip install python-decouple
```

2. Créez un fichier `.env` à la racine du projet :
```
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_application
```

3. Modifiez `settings.py` :
```python
from decouple import config

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

4. Ajoutez `.env` à votre `.gitignore` pour ne pas le commiter.

