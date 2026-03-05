"""
Email Provider Presets - ModularBEF

Configurazioni predefinite per i provider email più comuni.
Usate dal wizard di configurazione per facilitare il setup.
"""

EMAIL_PROVIDERS = {
    'gmail': {
        'name': 'Gmail',
        'description': 'Google Gmail / G Suite / Google Workspace',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False,
        'imap_server': 'imap.gmail.com',
        'imap_port': 993,
        'imap_use_tls': False,
        'imap_use_ssl': True,
        'help_url': 'https://support.google.com/mail/answer/7126229',
        'help_text': '''
            <h6>Configurazione Gmail</h6>
            <ol>
                <li>Vai su <a href="https://myaccount.google.com/security" target="_blank">Account Google → Sicurezza</a></li>
                <li>Attiva la "Verifica in due passaggi" se non l'hai già fatto</li>
                <li>Vai su "Password per le app"</li>
                <li>Seleziona "Posta" e "Altro dispositivo"</li>
                <li>Copia la password generata (16 caratteri)</li>
                <li>Usala come "Password SMTP" (NON la tua password Gmail normale)</li>
            </ol>
            <div class="alert alert-warning">
                <strong>⚠️ Importante:</strong> NON usare la tua password Gmail normale, ma solo le "Password per le app".
            </div>
        ''',
        'icon': 'bi-google',
        'color': '#EA4335',
    },
    'outlook': {
        'name': 'Outlook / Office 365',
        'description': 'Microsoft Outlook, Hotmail, Live, Office 365',
        'smtp_server': 'smtp-mail.outlook.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False,
        'imap_server': 'outlook.office365.com',
        'imap_port': 993,
        'imap_use_tls': False,
        'imap_use_ssl': True,
        'help_url': 'https://support.microsoft.com/it-it/office/impostazioni-pop-imap-e-smtp-per-outlook-com-d088b986-291d-42b8-9564-9c414e2aa040',
        'help_text': '''
            <h6>Configurazione Outlook/Office 365</h6>
            <ol>
                <li>Usa il tuo indirizzo email completo come username (es: nome@outlook.com)</li>
                <li>Usa la tua password normale di Outlook</li>
                <li>Se hai l'autenticazione a due fattori attiva:
                    <ul>
                        <li>Vai su <a href="https://account.microsoft.com/security" target="_blank">Account Microsoft → Sicurezza</a></li>
                        <li>Crea una "Password per app"</li>
                        <li>Usa quella password invece della tua password normale</li>
                    </ul>
                </li>
            </ol>
            <div class="alert alert-info">
                <strong>💡 Suggerimento:</strong> Per Office 365 aziendale, il server potrebbe essere diverso. Contatta il tuo IT.
            </div>
        ''',
        'icon': 'bi-microsoft',
        'color': '#0078D4',
    },
    'icloud': {
        'name': 'iCloud Mail',
        'description': 'Apple iCloud Mail (@icloud.com, @me.com)',
        'smtp_server': 'smtp.mail.me.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False,
        'imap_server': 'imap.mail.me.com',
        'imap_port': 993,
        'imap_use_tls': False,
        'imap_use_ssl': True,
        'help_url': 'https://support.apple.com/it-it/HT202304',
        'help_text': '''
            <h6>Configurazione iCloud Mail</h6>
            <ol>
                <li>Vai su <a href="https://appleid.apple.com" target="_blank">ID Apple → Sicurezza</a></li>
                <li>Nella sezione "Password specifiche per app", clicca su "Genera password"</li>
                <li>Inserisci un nome (es: "Sistema AMG")</li>
                <li>Copia la password generata (formato: xxxx-xxxx-xxxx-xxxx)</li>
                <li>Usala come "Password SMTP" (NON la tua password iCloud normale)</li>
            </ol>
            <div class="alert alert-warning">
                <strong>⚠️ Importante:</strong> Devi avere l'autenticazione a due fattori attiva per usare le password specifiche.
            </div>
        ''',
        'icon': 'bi-apple',
        'color': '#000000',
    },
    'yahoo': {
        'name': 'Yahoo Mail',
        'description': 'Yahoo Mail',
        'smtp_server': 'smtp.mail.yahoo.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False,
        'imap_server': 'imap.mail.yahoo.com',
        'imap_port': 993,
        'imap_use_tls': False,
        'imap_use_ssl': True,
        'help_url': 'https://help.yahoo.com/kb/SLN4075.html',
        'help_text': '''
            <h6>Configurazione Yahoo Mail</h6>
            <ol>
                <li>Vai su <a href="https://login.yahoo.com/account/security" target="_blank">Account Yahoo → Sicurezza</a></li>
                <li>Clicca su "Genera password app"</li>
                <li>Seleziona "Altra app" e inserisci un nome</li>
                <li>Copia la password generata</li>
                <li>Usala come "Password SMTP"</li>
            </ol>
        ''',
        'icon': 'bi-envelope',
        'color': '#6001D2',
    },
    'other': {
        'name': 'Altro Provider',
        'description': 'Configurazione manuale per altri provider email',
        'smtp_server': '',
        'smtp_port': 587,
        'use_tls': True,
        'use_ssl': False,
        'imap_server': '',
        'imap_port': 993,
        'imap_use_tls': False,
        'imap_use_ssl': True,
        'help_text': '''
            <h6>Configurazione Manuale</h6>
            <p>Contatta il tuo provider email per ottenere:</p>
            <ul>
                <li>Server SMTP (es: smtp.tuoprovider.com)</li>
                <li>Porta SMTP (solitamente 587 con TLS o 465 con SSL)</li>
                <li>Server IMAP (es: imap.tuoprovider.com)</li>
                <li>Porta IMAP (solitamente 993)</li>
                <li>Username e Password</li>
            </ul>
            <div class="alert alert-info">
                <strong>💡 Provider comuni:</strong>
                <ul>
                    <li><strong>Aruba:</strong> smtp.aruba.it:465 (SSL)</li>
                    <li><strong>Libero:</strong> smtp.libero.it:587 (TLS)</li>
                    <li><strong>Virgilio:</strong> out.virgilio.it:587 (TLS)</li>
                    <li><strong>Tiscali:</strong> smtp.tiscali.it:587 (TLS)</li>
                </ul>
            </div>
        ''',
        'icon': 'bi-envelope-at',
        'color': '#6c757d',
    },
}


def get_provider_config(provider_key):
    """
    Restituisce la configurazione per un provider specifico.
    
    Args:
        provider_key: Chiave del provider (gmail, outlook, icloud, yahoo, other)
    
    Returns:
        dict: Configurazione del provider o None se non trovato
    """
    return EMAIL_PROVIDERS.get(provider_key)


def get_all_providers():
    """
    Restituisce tutti i provider disponibili.
    
    Returns:
        dict: Dizionario di tutti i provider
    """
    return EMAIL_PROVIDERS
