# Guida Deploy su Heroku

## Preparazione Completata

Ho già preparato tutti i file necessari per Heroku:

- ✅ `Procfile` - Configurazione web server
- ✅ `runtime.txt` - Versione Python 3.11.11
- ✅ `requirements.txt` - Dipendenze aggiornate
- ✅ `app.json` - Configurazione app Heroku
- ✅ `settings.py` - Configurato per produzione
- ✅ `.env.example` - Template variabili d'ambiente
- ✅ `.slugignore` - File da ignorare nel deploy
- ✅ Heroku CLI installato
- ✅ Codice pushato su GitHub

## Deploy Automatico (Opzione 1 - CONSIGLIATO)

Esegui lo script automatico:

```cmd
deploy-heroku.bat
```

Lo script ti guiderà attraverso tutti i passaggi.

## Deploy Manuale (Opzione 2)

### 1. Login a Heroku

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" login
```

Questo aprirà il browser per l'autenticazione.

### 2. Crea l'app Heroku

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" create amg-gestionale-[tuo-nome]
```

Sostituisci `[tuo-nome]` con un identificativo univoco.

### 3. Aggiungi PostgreSQL

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" addons:create heroku-postgresql:essential-0
```

### 4. Configura le variabili d'ambiente

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" config:set DEBUG=False
"C:\Program Files\heroku\bin\heroku.cmd" config:set ALLOWED_HOSTS=[nome-app].herokuapp.com
"C:\Program Files\heroku\bin\heroku.cmd" config:set SECRET_KEY=[genera-chiave-sicura]
"C:\Program Files\heroku\bin\heroku.cmd" config:set EMAIL_HOST_USER=danigioloso@gmail.com
"C:\Program Files\heroku\bin\heroku.cmd" config:set EMAIL_HOST_PASSWORD=btllyzzspiwdhqhl
```

### 5. Deploy del codice

```cmd
git push heroku master
```

### 6. Esegui le migrazioni

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py migrate
```

### 7. Crea un superuser

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py createsuperuser
```

### 8. Apri l'app

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" open
```

## Comandi Utili

### Visualizza i log

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" logs --tail
```

### Riavvia l'app

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" restart
```

### Esegui comandi Django

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py [comando]
```

### Scala l'app

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" ps:scale web=1
```

### Visualizza lo stato

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" ps
```

## Note Importanti

1. **Database**: Heroku usa PostgreSQL invece di SQLite. Il database è già configurato automaticamente.

2. **File Media**: I file caricati dagli utenti non persistono su Heroku. Per file permanenti, considera:
   - AWS S3
   - Cloudinary
   - Google Cloud Storage

3. **Costi**:
   - Piano Essential PostgreSQL: ~$5/mese
   - Web dyno: Gratis con limitazioni o ~$7/mese per Basic

4. **Limiti Piano Gratuito**:
   - L'app si "addormenta" dopo 30 minuti di inattività
   - Tempo di risposta più lento al riavvio
   - 550-1000 ore dyno/mese

5. **Sicurezza**:
   - Il SECRET_KEY è già configurato per usare variabili d'ambiente
   - DEBUG è impostato a False in produzione
   - ALLOWED_HOSTS è configurato correttamente

## Troubleshooting

### Errore: "Application error"

```cmd
"C:\Program Files\heroku\bin\heroku.cmd" logs --tail
```

### Errore: "Build failed"

Verifica che requirements.txt sia corretto:
```cmd
git add requirements.txt
git commit -m "Fix requirements"
git push heroku master
```

### Database non trovato

Verifica che PostgreSQL sia aggiunto:
```cmd
"C:\Program Files\heroku\bin\heroku.cmd" addons
```

## Link Utili

- Dashboard Heroku: https://dashboard.heroku.com
- Repository GitHub: https://github.com/Giorgino79/AMG
- Documentazione Heroku Django: https://devcenter.heroku.com/articles/django-app-configuration
