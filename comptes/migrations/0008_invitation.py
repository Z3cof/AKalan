# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0007_change_note_cours_to_devoir'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('role', models.CharField(choices=[('admin', 'Administrateur'), ('enseignant', 'Enseignant'), ('etudiant', 'Étudiant')], max_length=20, verbose_name='Rôle')),
                ('token', models.CharField(max_length=64, unique=True, verbose_name='Token')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('acceptee', 'Acceptée'), ('expiree', 'Expirée')], default='en_attente', max_length=20, verbose_name='Statut')),
                ('date_creation', models.DateTimeField(auto_now_add=True, verbose_name="Date de création")),
                ('date_expiration', models.DateTimeField(verbose_name="Date d'expiration")),
                ('date_acceptation', models.DateTimeField(blank=True, null=True, verbose_name="Date d'acceptation")),
                ('classe', models.ForeignKey(blank=True, help_text='Uniquement pour les étudiants', null=True, on_delete=django.db.models.deletion.SET_NULL, to='comptes.classe', verbose_name='Classe')),
                ('cree_par', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invitations_creees', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
            ],
            options={
                'verbose_name': 'Invitation',
                'verbose_name_plural': 'Invitations',
                'ordering': ['-date_creation'],
            },
        ),
    ]

