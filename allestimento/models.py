from django.db import models
from django.conf import settings


class SessioneAllestimento(models.Model):
    """Sessione di allestimento - rappresenta un file Excel caricato"""

    nome_evento = models.CharField(max_length=255, blank=True)
    luogo = models.CharField(max_length=255, blank=True)
    file_originale = models.FileField(upload_to='allestimento/excel/', blank=True, null=True)
    data_creazione = models.DateTimeField(auto_now_add=True)
    data_completamento = models.DateTimeField(blank=True, null=True)
    completata = models.BooleanField(default=False)
    creato_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessioni_allestimento'
    )

    class Meta:
        verbose_name = 'Sessione Allestimento'
        verbose_name_plural = 'Sessioni Allestimento'
        ordering = ['-data_creazione']

    def __str__(self):
        return f"{self.nome_evento} - {self.data_creazione.strftime('%d/%m/%Y')}"

    @property
    def righe_completate(self):
        return self.righe.filter(completata=True).count()

    @property
    def righe_totali(self):
        return self.righe.count()

    @property
    def percentuale_completamento(self):
        if self.righe_totali == 0:
            return 0
        return int((self.righe_completate / self.righe_totali) * 100)


class RigaProdotto(models.Model):
    """Singola riga prodotto da allestire"""

    sessione = models.ForeignKey(
        SessioneAllestimento,
        on_delete=models.CASCADE,
        related_name='righe'
    )
    ordine = models.PositiveIntegerField(default=0)
    descrizione = models.CharField(max_length=500)
    quantita_richiesta = models.PositiveIntegerField(default=0)
    quantita_allestita = models.PositiveIntegerField(default=0)
    note = models.TextField(max_length=2000, blank=True)
    completata = models.BooleanField(default=False)
    data_completamento = models.DateTimeField(blank=True, null=True)
    completata_da = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='righe_completate'
    )

    class Meta:
        verbose_name = 'Riga Prodotto'
        verbose_name_plural = 'Righe Prodotto'
        ordering = ['ordine']

    def __str__(self):
        return f"{self.descrizione} ({self.quantita_richiesta})"

    @property
    def qr_data(self):
        """Dati da codificare nel QR code"""
        return f"PROD:{self.id}|{self.descrizione}|Q:{self.quantita_richiesta}"
