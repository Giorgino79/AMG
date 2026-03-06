from django.contrib import admin
from .models import *

# Automezzi
admin.site.register(Automezzo)
admin.site.register(Manutenzione)
admin.site.register(EventoAutomezzo)
admin.site.register(Rifornimento)
admin.site.register(AffidamentoMezzo)

# Gruppi Elettrogeni
admin.site.register(Gruppo)
admin.site.register(ManutenzioneGruppo)
admin.site.register(EventoGruppo)
admin.site.register(AffidamentoGruppo)
