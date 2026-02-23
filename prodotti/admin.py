# prodotti/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import TextInput, Textarea
from .models import Categoria, Prodotto 

admin.site.register(Prodotto)
admin.site.register(Categoria)