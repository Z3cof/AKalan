# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0002_cours_classe'),
        ('comptes', '0005_remove_classe_enseignant_classe_enseignants'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.DecimalField(decimal_places=2, help_text='Note sur 20', max_digits=5, verbose_name='Note')),
                ('commentaire', models.TextField(blank=True, null=True, verbose_name='Commentaire')),
                ('date_attribution', models.DateTimeField(auto_now_add=True, verbose_name="Date d'attribution")),
                ('cours', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='cours.cours', verbose_name='Cours')),
                ('enseignant', models.ForeignKey(limit_choices_to={'role': 'enseignant'}, on_delete=django.db.models.deletion.CASCADE, related_name='notes_attribuees', to=settings.AUTH_USER_MODEL, verbose_name='Enseignant')),
                ('etudiant', models.ForeignKey(limit_choices_to={'role': 'etudiant'}, on_delete=django.db.models.deletion.CASCADE, related_name='notes', to=settings.AUTH_USER_MODEL, verbose_name='Étudiant')),
            ],
            options={
                'verbose_name': 'Note',
                'verbose_name_plural': 'Notes',
                'ordering': ['-date_attribution'],
            },
        ),
    ]

