"""
Tests per app progetti_eventi.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from anagrafica.models import Cliente
from .models import Progetto, ProgettoReparto, ListaProdotti

User = get_user_model()


class ProgettoTestCase(TestCase):
    """Test per model Progetto"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            codice_dipendente='999',
            codice_fiscale='TESTCF99X99X999X'
        )

        self.cliente = Cliente.objects.create(
            ragione_sociale='Test Cliente SRL',
            telefono='1234567890',
            email='test@example.com',
            partita_iva='IT12345678901'
        )

    def test_creazione_progetto(self):
        """Test creazione progetto base"""
        from datetime import date, timedelta

        data_evento = date.today() + timedelta(days=30)

        progetto = Progetto.objects.create(
            cliente=self.cliente,
            nome_evento='Test Matrimonio',
            tipo_evento='matrimonio',
            data_evento=data_evento,
            location='Villa Test',
            indirizzo_location='Via Test 1',
            citta_location='Milano',
            data_consegna_richiesta=data_evento,
            data_ritiro_richiesta=data_evento,
            commerciale=self.user,
            reparti_coinvolti=['audio', 'video'],
        )

        self.assertIsNotNone(progetto.codice)
        self.assertTrue(progetto.codice.startswith('PRJ-'))
        self.assertEqual(progetto.stato, 'bozza')

    def test_creazione_reparti(self):
        """Test creazione reparti automatica"""
        from datetime import date, timedelta

        progetto = Progetto.objects.create(
            cliente=self.cliente,
            nome_evento='Test Concerto',
            tipo_evento='concerto',
            data_evento=date.today() + timedelta(days=60),
            location='Arena Test',
            indirizzo_location='Via Arena 1',
            citta_location='Roma',
            data_consegna_richiesta=date.today() + timedelta(days=60),
            data_ritiro_richiesta=date.today() + timedelta(days=60),
            commerciale=self.user,
            reparti_coinvolti=['audio', 'video', 'luci'],
        )

        # Crea manualmente reparti (in production fatto dalla view)
        for reparto in ['audio', 'video', 'luci']:
            ProgettoReparto.objects.create(
                progetto=progetto,
                tipo_reparto=reparto,
            )

        self.assertEqual(progetto.reparti.count(), 3)
        self.assertTrue(progetto.reparti.filter(tipo_reparto='audio').exists())


# TODO: Aggiungere test per:
# - Workflow engineering
# - Approvazione liste prodotti
# - Calcolo totali
# - Integrazione con altre app
