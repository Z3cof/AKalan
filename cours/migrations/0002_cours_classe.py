# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0001_initial'),
        ('comptes', '0005_remove_classe_enseignant_classe_enseignants'),
    ]

    operations = [
        migrations.AddField(
            model_name='cours',
            name='classe',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cours', to='comptes.classe', verbose_name='Classe'),
        ),
    ]

