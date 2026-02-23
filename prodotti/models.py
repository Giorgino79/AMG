# prodotti/models.py
"""
PRODOTTI - Anagrafica Prodotti
==============================

App per la gestione anagrafica dei prodotti.
NON gestisce: scorte (app magazzino), prezzi (app listino)
"""

from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from decimal import Decimal
import os
import uuid
import hashlib


def upload_categoria_icon(instance, filename):
    """Percorso upload per icone categorie"""
    ext = filename.split(".")[-1]
    return os.path.join("categorie/icone", f"{instance.nome_categoria}.{ext}")


def upload_prodotto_image(instance, filename):
    """Percorso upload per immagini prodotti"""
    ext = filename.split(".")[-1]
    return os.path.join("prodotti/immagini", f"{instance.nome_prodotto}.{ext}")


def upload_qrcode_image(instance, filename):
    """Percorso upload per QR code"""
    ext = filename.split(".")[-1]
    return os.path.join("prodotti/qrcode", f"qr_{instance.pk or 'new'}.{ext}")


def upload_barcode_image(instance, filename):
    """Percorso upload per barcode"""
    ext = filename.split(".")[-1]
    return os.path.join("prodotti/barcode", f"bc_{instance.pk or 'new'}.{ext}")


class Categoria(models.Model):
    """Categoria di prodotti"""

    nome_categoria = models.CharField(
        _("Nome Categoria"),
        max_length=200,
        unique=True,
        help_text="Nome della categoria di prodotti",
    )
    icona = models.ImageField(
        _("Icona"),
        upload_to=upload_categoria_icon,
        blank=True,
        null=True,
        help_text="Icona rappresentativa della categoria",
    )
    descrizione = models.TextField(
        _("Descrizione"),
        blank=True,
        help_text="Descrizione dettagliata della categoria",
    )
    attiva = models.BooleanField(
        _("Attiva"), default=True, help_text="Indica se la categoria è attiva"
    )

    # Timestamp
    created_at = models.DateTimeField(_("Creato il"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Aggiornato il"), auto_now=True)

    class Meta:
        verbose_name = _("Categoria")
        verbose_name_plural = _("Categorie")
        ordering = ["nome_categoria"]

    def __str__(self):
        return self.nome_categoria

    def get_absolute_url(self):
        return reverse("prodotti:categoria_detail", kwargs={"pk": self.pk})

    @property
    def prodotti_count(self):
        """Numero di prodotti attivi nella categoria"""
        return self.prodotti.filter(attivo=True).count()


class Prodotto(models.Model):
    """
    Anagrafica Prodotto

    Gestisce solo i dati anagrafici del prodotto.
    Scorte gestite da app magazzino, prezzi da app listino.
    """

    class Misura(models.TextChoices):
        BOTTIGLIA = "bottiglia", _("Vendita a bottiglia")
        KILO = "kilo", _("Vendita al peso (kg)")
        LITRO = "litro", _("Vendita al litro")
        CONFEZIONE = "confezione", _("Vendita a confezione")
        PEZZO = "pezzo", _("Vendita a pezzo")
        METRO = "metro", _("Vendita al metro")
        METRO_QUADRO = "mq", _("Vendita a metro quadro")

    class AliquotaIva(models.TextChoices):
        QUATTRO = "4", _("IVA 4%")
        DIECI = "10", _("IVA 10%")
        VENTIDUE = "22", _("IVA 22%")

    class TipoProdotto(models.TextChoices):
        FISICO = "fisico", _("Prodotto fisico")
        SERVIZIO = "servizio", _("Servizio")
        DIGITALE = "digitale", _("Prodotto digitale")

    # === RELAZIONI ===
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="prodotti",
        verbose_name=_("Categoria"),
    )

    # Fornitore principale (opzionale - prodotti multi-fornitore non lo usano)
    fornitore_principale = models.ForeignKey(
        'anagrafica.Fornitore',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prodotti",
        verbose_name=_("Fornitore Principale"),
        help_text="Fornitore principale del prodotto (opzionale per prodotti multi-fornitore)"
    )

    # === INFORMAZIONI DI BASE ===
    nome_prodotto = models.CharField(
        _("Nome Prodotto"),
        max_length=200,
        help_text="Nome commerciale del prodotto"
    )
    descrizione_breve = models.CharField(
        _("Descrizione Breve"),
        max_length=500,
        blank=True,
        help_text="Descrizione breve per listini",
    )
    descrizione_completa = models.TextField(
        _("Descrizione Completa"),
        blank=True,
        help_text="Descrizione dettagliata del prodotto",
    )

    # === CODICI IDENTIFICATIVI ===
    # EAN opzionale - validazione solo se richiesto
    ean = models.CharField(
        _("Codice EAN"),
        max_length=13,
        blank=True,
        help_text="Codice a barre EAN-13 (opzionale)",
    )
    codice_interno = models.CharField(
        _("Codice Interno"),
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        help_text="Codice interno aziendale",
    )
    codice_fornitore = models.CharField(
        _("Codice Fornitore"),
        max_length=50,
        blank=True,
        help_text="Codice utilizzato dal fornitore",
    )

    # === QR CODE E BARCODE ===
    qrcode_data = models.CharField(
        _("Dati QR Code"),
        max_length=500,
        blank=True,
        help_text="Contenuto del QR code (generato automaticamente o importato)"
    )
    qrcode_image = models.ImageField(
        _("Immagine QR Code"),
        upload_to=upload_qrcode_image,
        blank=True,
        null=True,
        help_text="Immagine QR code (generata o importata)"
    )
    barcode_data = models.CharField(
        _("Dati Barcode"),
        max_length=100,
        blank=True,
        help_text="Contenuto del barcode (EAN o personalizzato)"
    )
    barcode_image = models.ImageField(
        _("Immagine Barcode"),
        upload_to=upload_barcode_image,
        blank=True,
        null=True,
        help_text="Immagine barcode (generata o importata)"
    )

    # === CARATTERISTICHE FISICHE ===
    tipo_prodotto = models.CharField(
        _("Tipo Prodotto"),
        max_length=10,
        choices=TipoProdotto.choices,
        default=TipoProdotto.FISICO,
    )
    misura = models.CharField(
        _("Unità di Misura"),
        max_length=15,
        choices=Misura.choices,
        default=Misura.PEZZO,
    )
    peso_netto = models.DecimalField(
        _("Peso Netto (kg)"),
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    peso_lordo = models.DecimalField(
        _("Peso Lordo (kg)"),
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    volume = models.DecimalField(
        _("Volume (litri)"),
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.001"))],
    )
    dimensioni = models.CharField(
        _("Dimensioni"),
        max_length=100,
        blank=True,
        help_text="Es: 10x5x3 cm"
    )

    # === ASPETTI FISCALI ===
    aliquota_iva = models.CharField(
        _("Aliquota IVA"),
        max_length=3,
        choices=AliquotaIva.choices,
        default=AliquotaIva.VENTIDUE,
    )

    # === STATO E METADATI ===
    attivo = models.BooleanField(_("Attivo"), default=True)
    novita = models.BooleanField(_("Novità"), default=False)
    in_evidenza = models.BooleanField(_("In Evidenza"), default=False)
    merce_deperibile = models.BooleanField(
        _("Merce Deperibile"),
        default=False,
        help_text="Indica se il prodotto è deperibile"
    )

    # === MEDIA ===
    immagine = models.ImageField(
        _("Immagine"),
        upload_to=upload_prodotto_image,
        blank=True,
        null=True
    )

    # === NOTE ===
    note_interne = models.TextField(
        _("Note Interne"),
        blank=True,
        help_text="Note visibili solo internamente"
    )

    # === TIMESTAMP ===
    created_at = models.DateTimeField(_("Creato il"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Aggiornato il"), auto_now=True)

    class Meta:
        verbose_name = _("Prodotto")
        verbose_name_plural = _("Prodotti")
        ordering = ["nome_prodotto"]
        indexes = [
            models.Index(fields=["ean"]),
            models.Index(fields=["codice_interno"]),
            models.Index(fields=["categoria", "attivo"]),
            models.Index(fields=["attivo", "nome_prodotto"]),
            models.Index(fields=["fornitore_principale"]),
        ]

    def __str__(self):
        return self.nome_prodotto

    def get_absolute_url(self):
        return reverse("prodotti:prodotto_detail", kwargs={"pk": self.pk})

    @property
    def nome_completo(self):
        """Nome prodotto con codice interno se disponibile"""
        if self.codice_interno:
            return f"{self.codice_interno} - {self.nome_prodotto}"
        return self.nome_prodotto

    @property
    def has_qrcode(self):
        """Verifica se il prodotto ha un QR code"""
        return bool(self.qrcode_image) or bool(self.qrcode_data)

    @property
    def has_barcode(self):
        """Verifica se il prodotto ha un barcode"""
        return bool(self.barcode_image) or bool(self.barcode_data)

    def generate_qrcode_data(self):
        """
        Genera i dati per il QR code basati sul prodotto.
        Restituisce una stringa con le info del prodotto.
        """
        data_parts = [f"PROD:{self.pk}"]
        if self.codice_interno:
            data_parts.append(f"COD:{self.codice_interno}")
        if self.ean:
            data_parts.append(f"EAN:{self.ean}")
        data_parts.append(f"NAME:{self.nome_prodotto[:50]}")
        return "|".join(data_parts)

    def validate_ean(self):
        """
        Valida il codice EAN-13 (controllo checksum).
        Restituisce (is_valid, message)
        """
        if not self.ean:
            return True, "Nessun EAN da validare"

        # Controllo formato
        if not self.ean.isdigit() or len(self.ean) != 13:
            return False, "EAN deve essere di 13 cifre numeriche"

        # Controllo checksum EAN-13
        digits = [int(d) for d in self.ean]
        checksum = 0
        for i, digit in enumerate(digits[:-1]):
            if i % 2 == 0:
                checksum += digit
            else:
                checksum += digit * 3

        calculated_check = (10 - (checksum % 10)) % 10

        if calculated_check != digits[-1]:
            return False, f"Checksum EAN non valido (atteso: {calculated_check})"

        return True, "EAN valido"

    def save(self, *args, **kwargs):
        """Override save per generare QR data se necessario"""
        # Se non c'è qrcode_data ma il prodotto ha un pk, genera i dati
        if self.pk and not self.qrcode_data:
            self.qrcode_data = self.generate_qrcode_data()

        # Se c'è EAN, usalo come barcode_data se non specificato
        if self.ean and not self.barcode_data:
            self.barcode_data = self.ean

        super().save(*args, **kwargs)

        # Dopo il primo save, genera qrcode_data se non esisteva
        if not self.qrcode_data:
            self.qrcode_data = self.generate_qrcode_data()
            super().save(update_fields=['qrcode_data'])
