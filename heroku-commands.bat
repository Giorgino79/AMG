@echo off
REM Comandi Rapidi Heroku per AMG-ROMA

:menu
cls
echo ========================================
echo COMANDI HEROKU - AMG ROMA
echo ========================================
echo.
echo 1. Visualizza log in tempo reale
echo 2. Crea superuser
echo 3. Apri app nel browser
echo 4. Verifica stato app
echo 5. Esegui migrazioni
echo 6. Verifica configurazione
echo 7. Riavvia app
echo 8. Scala web dyno
echo 9. Shell Django remoto
echo 10. Visualizza database info
echo 0. Esci
echo.
set /p choice="Scegli opzione (0-10): "

if "%choice%"=="1" goto logs
if "%choice%"=="2" goto createsuperuser
if "%choice%"=="3" goto open
if "%choice%"=="4" goto status
if "%choice%"=="5" goto migrate
if "%choice%"=="6" goto config
if "%choice%"=="7" goto restart
if "%choice%"=="8" goto scale
if "%choice%"=="9" goto shell
if "%choice%"=="10" goto dbinfo
if "%choice%"=="0" goto end
goto menu

:logs
echo.
echo Visualizzazione log in tempo reale (CTRL+C per uscire)...
"C:\Program Files\heroku\bin\heroku.cmd" logs --tail -a amg-roma
pause
goto menu

:createsuperuser
echo.
echo Creazione superuser...
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py createsuperuser -a amg-roma
pause
goto menu

:open
echo.
echo Apertura app nel browser...
"C:\Program Files\heroku\bin\heroku.cmd" open -a amg-roma
pause
goto menu

:status
echo.
echo Stato app:
"C:\Program Files\heroku\bin\heroku.cmd" ps -a amg-roma
echo.
echo Info app:
"C:\Program Files\heroku\bin\heroku.cmd" apps:info -a amg-roma
pause
goto menu

:migrate
echo.
echo Esecuzione migrazioni...
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py migrate -a amg-roma
pause
goto menu

:config
echo.
echo Configurazione ambiente:
"C:\Program Files\heroku\bin\heroku.cmd" config -a amg-roma
pause
goto menu

:restart
echo.
echo Riavvio app...
"C:\Program Files\heroku\bin\heroku.cmd" restart -a amg-roma
echo App riavviata!
pause
goto menu

:scale
echo.
echo Scaling web dyno...
set /p dynos="Numero di dyno web (1-10): "
"C:\Program Files\heroku\bin\heroku.cmd" ps:scale web=%dynos% -a amg-roma
pause
goto menu

:shell
echo.
echo Apertura shell Django remoto...
"C:\Program Files\heroku\bin\heroku.cmd" run python manage.py shell -a amg-roma
pause
goto menu

:dbinfo
echo.
echo Informazioni database PostgreSQL:
"C:\Program Files\heroku\bin\heroku.cmd" pg:info -a amg-roma
echo.
echo Credenziali database:
"C:\Program Files\heroku\bin\heroku.cmd" pg:credentials:url -a amg-roma
pause
goto menu

:end
echo.
echo Arrivederci!
exit /b 0
