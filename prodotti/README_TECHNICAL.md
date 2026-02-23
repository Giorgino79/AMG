# prodotti - Documentazione Tecnica

## Versione
- **Versione corrente**: 1.0.0
- **Django**: 5.1.4
- **Python**: 3.9+

## Descrizione
[Descrizione tecnica del modulo]

## Architettura

### Modelli
- `Item`: [Descrizione]
  - Eredita da: `BaseModel`
  - Mixin utilizzati: [AllegatiMixin, PDFMixin, etc.]
  - Campi principali: [...]
  - Relazioni: [...]

### View
- `ItemListView`: Lista paginata con ricerca
- `ItemDetailView`: Dettaglio con allegati/QR
- `ItemCreateView`: Creazione
- `ItemUpdateView`: Modifica
- `ItemDeleteView`: Eliminazione (soft delete)

### Form
- `ItemForm`: ModelForm con validazione custom

### URL
- `prodotti:Item_lower_list` → Lista
- `prodotti:Item_lower_detail` → Dettaglio
- `prodotti:Item_lower_create` → Creazione
- `prodotti:Item_lower_update` → Modifica
- `prodotti:Item_lower_delete` → Eliminazione

## Dipendenze
### Moduli Required
- `core` (v1.0.0+)
- `users` (v1.0.0+)

### Moduli Optional
- [Lista moduli opzionali]

## Database
### Tabelle
- `prodotti_Item_lower`

### Migrazioni
```bash
python manage.py makemigrations prodotti
python manage.py migrate prodotti
```

## Configurazione

### Settings.py
```python
INSTALLED_APPS = [
    # ...
    'prodotti',
]
```

### URLs
```python
path('prodotti/', include('prodotti.urls')),
```

## API Endpoints
[Se presente API REST]

## Template
- Estende: `commons_templates/base_detail.html`
- Template tag utilizzati: `{% load allegati_tags %}`

## Permessi
- `prodotti.view_Item_lower`
- `prodotti.add_Item_lower`
- `prodotti.change_Item_lower`
- `prodotti.delete_Item_lower`

## Testing
```bash
pytest prodotti/tests/
```

## Troubleshooting
[Problemi comuni e soluzioni]

## Changelog
Vedi [CHANGELOG.md](./CHANGELOG.md)
