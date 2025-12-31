# Generated manually
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devoirs', '0001_initial'),
        ('comptes', '0006_note'),
    ]

    operations = [
        # Supprimer toutes les notes existantes car elles n'ont pas de devoir associé
        migrations.RunSQL(
            "DELETE FROM comptes_note;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Supprimer l'ancien champ cours
        migrations.RemoveField(
            model_name='note',
            name='cours',
        ),
        # Ajouter le nouveau champ devoir (obligatoire)
        migrations.AddField(
            model_name='note',
            name='devoir',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notes',
                to='devoirs.devoir',
                verbose_name='Devoir',
            ),
        ),
    ]
