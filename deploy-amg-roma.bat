@echo off
echo ========================================
echo Deploy AMG-ROMA su Heroku
echo ========================================
echo.

REM Login a Heroku
echo Step 1: Login a Heroku
echo Apriro il browser per l'autenticazione...
echo.
"C:\Program Files\heroku\bin\heroku.cmd" login
if errorlevel 1 (
    echo Errore durante il login
    pause
    exit /b 1
)

echo.
echo Step 2: Verifica app Heroku
"C:\Program Files\heroku\bin\heroku.cmd" apps:info -a amg-roma

echo.
echo Step 3: Verifica PostgreSQL
"C:\Program Files\heroku\bin\heroku.cmd" addons -a amg-roma

echo.
echo Step 4: Configura variabili d'ambiente
"C:\Program Files\heroku\bin\heroku.cmd" config:set DEBUG=False -a amg-roma
"C:\Program Files\heroku\bin\heroku.cmd" config:set ALLOWED_HOSTS=amg-roma.herokuapp.com -a amg-roma
"C:\Program Files\heroku\bin\heroku.cmd" config:set EMAIL_HOST_USER=danigioloso@gmail.com -a amg-roma
"C:\Program Files\heroku\bin\heroku.cmd" config:set EMAIL_HOST_PASSWORD=btllyzzspiwdhqhl -a amg-roma

echo.
echo Step 5: Verifica remote git
git remote -v

echo.
echo Step 6: Deploy su Heroku
echo Questo puo richiedere alcuni minuti...
git push heroku master
if errorlevel 1 (
    echo.
    echo Errore durante il push!
    echo Controlla i log sopra per dettagli.
    pause
    exit /b 1
)

echo.
echo Step 7: Verifica build
"C:\Program Files\heroku\bin\heroku.cmd" releases -a amg-roma

echo.
echo Step 8: Esegui migrazione database
echo Eseguo le migrazioni...
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py migrate -a amg-roma
if errorlevel 1 (
    echo Errore durante le migrazioni
    pause
    exit /b 1
)

echo.
echo Step 9: Raccogli file statici
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py collectstatic --noinput -a amg-roma

echo.
echo ========================================
echo Deploy completato con successo!
echo ========================================
echo.
echo App URL: https://amg-roma.herokuapp.com
echo Dashboard: https://dashboard.heroku.com/apps/amg-roma
echo.
echo Per creare un superuser:
echo "C:\Program Files\heroku\bin\heroku.cmd" run python manage.py createsuperuser -a amg-roma
echo.
echo Per vedere i log in tempo reale:
echo "C:\Program Files\heroku\bin\heroku.cmd" logs --tail -a amg-roma
echo.
echo Per aprire l'app nel browser:
echo "C:\Program Files\heroku\bin\heroku.cmd" open -a amg-roma
echo.

pause
