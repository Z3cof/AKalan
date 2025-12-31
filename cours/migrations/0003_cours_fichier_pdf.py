# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cours', '0002_cours_classe'),
    ]

    operations = [
        migrations.AddField(
            model_name='cours',
            name='fichier_pdf',
            field=models.FileField(blank=True, null=True, upload_to='cours/pdf/', verbose_name='Fichier PDF'),
        ),
    ]

