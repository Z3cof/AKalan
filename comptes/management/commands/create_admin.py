from django.core.management.base import BaseCommand
from comptes.models import Utilisateur


class Command(BaseCommand):
    help = 'Crée un utilisateur administrateur'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nom d\'utilisateur')
        parser.add_argument('--email', type=str, help='Email')
        parser.add_argument('--password', type=str, help='Mot de passe')

    def handle(self, *args, **options):
        username = options.get('username') or input('Nom d\'utilisateur: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Mot de passe: ')

        if Utilisateur.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'L\'utilisateur "{username}" existe déjà.'))
            return

        user = Utilisateur.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='admin'
        )
        self.stdout.write(self.style.SUCCESS(f'Administrateur "{username}" créé avec succès!'))

