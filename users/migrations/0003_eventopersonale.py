# Generated migration for EventoPersonale model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_codice_fiscale'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventoPersonale',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creato il')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aggiornato il')),
                ('deleted_at', models.DateTimeField(blank=True, editable=False, null=True, verbose_name='Eliminato il')),
                ('is_deleted', models.BooleanField(default=False, editable=False, verbose_name='Eliminato')),
                ('titolo', models.CharField(max_length=200, verbose_name='Titolo')),
                ('descrizione', models.TextField(blank=True, verbose_name='Descrizione')),
                ('tipo', models.CharField(choices=[('promemoria', 'Promemoria'), ('appuntamento', 'Appuntamento'), ('compleanno', 'Compleanno'), ('scadenza', 'Scadenza'), ('altro', 'Altro')], default='promemoria', max_length=20, verbose_name='Tipo')),
                ('priorita', models.CharField(choices=[('bassa', 'Bassa'), ('media', 'Media'), ('alta', 'Alta')], default='media', max_length=10, verbose_name='Priorità')),
                ('data_inizio', models.DateTimeField(verbose_name='Data/Ora Inizio')),
                ('data_fine', models.DateTimeField(blank=True, null=True, verbose_name='Data/Ora Fine')),
                ('tutto_il_giorno', models.BooleanField(default=False, verbose_name='Tutto il giorno')),
                ('ricorrente', models.BooleanField(default=False, verbose_name='Ricorrente')),
                ('notifica_email', models.BooleanField(default=False, verbose_name='Notifica via email')),
                ('colore', models.CharField(default='#007bff', help_text='Colore in formato esadecimale (es. #007bff)', max_length=7, verbose_name='Colore')),
                ('completato', models.BooleanField(default=False, verbose_name='Completato')),
                ('data_completamento', models.DateTimeField(blank=True, null=True, verbose_name='Data completamento')),
                ('utente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eventi_personali', to=settings.AUTH_USER_MODEL, verbose_name='Utente')),
            ],
            options={
                'verbose_name': 'Evento Personale',
                'verbose_name_plural': 'Eventi Personali',
                'db_table': 'users_evento_personale',
                'ordering': ['data_inizio'],
                'indexes': [models.Index(fields=['utente', 'data_inizio'], name='users_event_utente__idx'), models.Index(fields=['tipo'], name='users_event_tipo_idx'), models.Index(fields=['completato'], name='users_event_complet_idx')],
                'permissions': [('view_own_eventi', 'Può visualizzare i propri eventi personali'), ('manage_own_eventi', 'Può gestire i propri eventi personali')],
            },
        ),
    ]
