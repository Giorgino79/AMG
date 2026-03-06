from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AffidamentoMezzo, EventoAutomezzo
from datetime import date


@receiver(post_save, sender=AffidamentoMezzo)
def aggiorna_mappa_danni_affidamento(sender, instance, created, **kwargs):
    """Aggiorna la mappa danni del veicolo quando si completa un affidamento"""
    if instance.automezzo and instance.stato == 'completato' and instance.danni_rientro:
        # Aggiungi i nuovi danni alla mappa storica del veicolo
        automezzo = instance.automezzo
        mappa_danni = automezzo.mappa_danni if automezzo.mappa_danni else []

        # Aggiungi i danni del rientro con metadati
        for danno in instance.danni_rientro:
            # Verifica se il danno non è già presente (basandoci su posizione simile)
            danno_esistente = any(
                d.get('area') == danno.get('area') and
                abs(d.get('x', 0) - danno.get('x', 0)) < 10 and
                abs(d.get('y', 0) - danno.get('y', 0)) < 10
                for d in mappa_danni
            )

            if not danno_esistente:
                danno_con_meta = danno.copy()
                danno_con_meta['data'] = instance.data_rientro_effettivo.isoformat() if instance.data_rientro_effettivo else date.today().isoformat()
                danno_con_meta['fonte'] = f'Affidamento #{instance.id}'
                mappa_danni.append(danno_con_meta)

        automezzo.mappa_danni = mappa_danni
        automezzo.save(update_fields=['mappa_danni'])


@receiver(post_save, sender=EventoAutomezzo)
def aggiorna_mappa_danni_evento(sender, instance, created, **kwargs):
    """Aggiorna la mappa danni del veicolo quando si registra un evento con danni"""
    if instance.automezzo and instance.danni and (instance.tipo == 'incidente' or instance.tipo == 'guasto'):
        automezzo = instance.automezzo
        mappa_danni = automezzo.mappa_danni if automezzo.mappa_danni else []

        # Aggiungi i danni dell'evento con metadati
        for danno in instance.danni:
            # Verifica se il danno non è già presente
            danno_esistente = any(
                d.get('area') == danno.get('area') and
                abs(d.get('x', 0) - danno.get('x', 0)) < 10 and
                abs(d.get('y', 0) - danno.get('y', 0)) < 10
                for d in mappa_danni
            )

            if not danno_esistente:
                danno_con_meta = danno.copy()
                danno_con_meta['data'] = instance.data_evento.isoformat()
                danno_con_meta['fonte'] = f'Evento {instance.get_tipo_display()} #{instance.id}'
                mappa_danni.append(danno_con_meta)

        automezzo.mappa_danni = mappa_danni
        automezzo.save(update_fields=['mappa_danni'])
