# AMG - Quick Start Guide

## ✅ Completato

### GitHub
- ✅ Repository inizializzato
- ✅ Codice committato (386 file, 83.000+ righe)
- ✅ Pushato su: https://github.com/Giorgino79/AMG.git
- ✅ Configurazione Heroku aggiunta

### Heroku
- ✅ Heroku CLI installato
- ✅ File di configurazione creati
- ✅ Script di deploy automatico pronto

## 🚀 Prossimi Passi per Deploy Heroku

### Metodo Rapido (CONSIGLIATO)

1. Apri il terminale nella cartella del progetto
2. Esegui lo script:
   ```cmd
   deploy-heroku.bat
   ```
3. Segui le istruzioni a schermo

### Cosa Farà lo Script

1. Login a Heroku (aprirà il browser)
2. Creerà l'app Heroku
3. Aggiungerà PostgreSQL
4. Configurerà le variabili d'ambiente
5. Farà il deploy del codice
6. Eseguirà le migrazioni database
7. Ti permetterà di creare un superuser

### Dopo il Deploy

L'app sarà disponibile su:
```
https://[nome-app].herokuapp.com
```

## 📚 Documentazione

- **DEPLOY-HEROKU.md** - Guida completa deploy Heroku
- **README.md** - Documentazione completa del progetto
- **.env.example** - Template variabili d'ambiente

## 🔑 Credenziali Email

Email SMTP già configurata:
- Host: smtp.gmail.com
- User: danigioloso@gmail.com
- Password: configurata

## ⚙️ Configurazione Locale

Per testare in locale:

```cmd
# Attiva virtual environment
venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt

# Migrazioni
python manage.py migrate

# Crea superuser
python manage.py createsuperuser

# Avvia server
python manage.py runserver
```

## 🆘 Supporto

In caso di problemi:

1. Controlla i log: `heroku logs --tail`
2. Verifica la configurazione: `heroku config`
3. Consulta DEPLOY-HEROKU.md per troubleshooting

## 🔗 Link Utili

- GitHub: https://github.com/Giorgino79/AMG.git
- Heroku Dashboard: https://dashboard.heroku.com
- Documentazione Django: https://docs.djangoproject.com

---

**Buon deploy! 🎉**
