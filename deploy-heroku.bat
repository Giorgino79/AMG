@echo off
echo ========================================
echo Deploy AMG su Heroku
echo ========================================
echo.

REM Login a Heroku
echo Step 1: Login a Heroku
"C:\Program Files\heroku\bin\heroku.cmd" login
if errorlevel 1 (
    echo Errore durante il login
    pause
    exit /b 1
)

echo.
echo Step 2: Crea app Heroku (inserisci un nome univoco)
set /p APP_NAME="Nome app Heroku (es: amg-gestionale-[tuo-nome]): "
"C:\Program Files\heroku\bin\heroku.cmd" create %APP_NAME%
if errorlevel 1 (
    echo App già esistente o errore. Provo a usare l'app esistente...
)

echo.
echo Step 3: Aggiungi PostgreSQL
"C:\Program Files\heroku\bin\heroku.cmd" addons:create heroku-postgresql:essential-0 -a %APP_NAME%

echo.
echo Step 4: Configura variabili d'ambiente
"C:\Program Files\heroku\bin\heroku.cmd" config:set DEBUG=False -a %APP_NAME%
"C:\Program Files\heroku\bin\heroku.cmd" config:set ALLOWED_HOSTS=%APP_NAME%.herokuapp.com -a %APP_NAME%
"C:\Program Files\heroku\bin\heroku.cmd" config:set SECRET_KEY="%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%" -a %APP_NAME%
"C:\Program Files\heroku\bin\heroku.cmd" config:set EMAIL_HOST_USER=danigioloso@gmail.com -a %APP_NAME%
"C:\Program Files\heroku\bin\heroku.cmd" config:set EMAIL_HOST_PASSWORD=btllyzzspiwdhqhl -a %APP_NAME%

echo.
echo Step 5: Deploy su Heroku
git push heroku master
if errorlevel 1 (
    echo Errore durante il push
    pause
    exit /b 1
)

echo.
echo Step 6: Esegui migrazione database
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py migrate -a %APP_NAME%

echo.
echo Step 7: Crea superuser
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py createsuperuser -a %APP_NAME%

echo.
echo ========================================
echo Deploy completato!
echo App URL: https://%APP_NAME%.herokuapp.com
echo ========================================
echo.
echo Per aprire l'app nel browser:
"C:\Program Files\heroku\bin\heroku.cmd" open -a %APP_NAME%

pause
