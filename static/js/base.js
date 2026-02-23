/**
 * JavaScript base per ModularBEF
 * Gestisce sidebar, tools (calcolatrice, calendario), navigazione
 */

(function() {
    'use strict';

    // ========================================================================
    // INIZIALIZZAZIONE
    // ========================================================================
    document.addEventListener('DOMContentLoaded', function() {
        initSidebar();
        initCalcolatrice();
        initCalendario();
        initProfiloLink();
        initDateTime();
    });

    // ========================================================================
    // SIDEBAR TOGGLE (Mobile)
    // ========================================================================
    function initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebarToggle');
        const sidebarToggleMobile = document.getElementById('sidebarToggleMobile');

        if (!sidebar) return;

        // Toggle da bottone in sidebar
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', function() {
                sidebar.classList.toggle('show');

                // Cambia icona
                const icon = this.querySelector('i');
                if (sidebar.classList.contains('show')) {
                    icon.className = 'bi bi-chevron-right';
                } else {
                    icon.className = 'bi bi-chevron-left';
                }
            });
        }

        // Toggle da navbar (mobile)
        if (sidebarToggleMobile) {
            sidebarToggleMobile.addEventListener('click', function() {
                sidebar.classList.toggle('show');
            });
        }

        // Chiudi sidebar al click fuori (solo mobile)
        document.addEventListener('click', function(e) {
            if (window.innerWidth < 992) {
                if (!sidebar.contains(e.target) &&
                    !sidebarToggleMobile.contains(e.target) &&
                    sidebar.classList.contains('show')) {
                    sidebar.classList.remove('show');
                }
            }
        });

        // Evidenzia link attivo in base all'URL corrente
        highlightActiveLink();
    }

    function highlightActiveLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar .nav-link');

        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    // ========================================================================
    // CALCOLATRICE
    // ========================================================================
    function initCalcolatrice() {
        const calcBtn = document.getElementById('calcolatriceBtn');
        const calcModal = document.getElementById('calcolatriceModal');

        if (!calcBtn || !calcModal) return;

        const modal = new bootstrap.Modal(calcModal);
        const display = document.getElementById('calcDisplay');
        let currentValue = '0';
        let previousValue = null;
        let operation = null;

        // Apri modal
        calcBtn.addEventListener('click', function(e) {
            e.preventDefault();
            modal.show();
            resetCalcolatrice();
        });

        // Event listener bottoni calcolatrice
        document.querySelectorAll('.calc-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                handleCalcInput(value);
            });
        });

        function handleCalcInput(value) {
            if (value === 'C') {
                resetCalcolatrice();
            } else if (value === '=') {
                calculate();
            } else if (['+', '-', '*', '/'].includes(value)) {
                setOperation(value);
            } else if (value === '.') {
                if (!currentValue.includes('.')) {
                    currentValue += '.';
                    updateDisplay();
                }
            } else {
                // Numero
                if (currentValue === '0') {
                    currentValue = value;
                } else {
                    currentValue += value;
                }
                updateDisplay();
            }
        }

        function resetCalcolatrice() {
            currentValue = '0';
            previousValue = null;
            operation = null;
            updateDisplay();
        }

        function setOperation(op) {
            if (previousValue !== null && operation !== null) {
                calculate();
            }
            previousValue = parseFloat(currentValue);
            operation = op;
            currentValue = '0';
        }

        function calculate() {
            if (previousValue === null || operation === null) return;

            const current = parseFloat(currentValue);
            let result = 0;

            switch (operation) {
                case '+':
                    result = previousValue + current;
                    break;
                case '-':
                    result = previousValue - current;
                    break;
                case '*':
                    result = previousValue * current;
                    break;
                case '/':
                    if (current === 0) {
                        alert('Errore: divisione per zero');
                        resetCalcolatrice();
                        return;
                    }
                    result = previousValue / current;
                    break;
            }

            currentValue = result.toString();
            previousValue = null;
            operation = null;
            updateDisplay();
        }

        function updateDisplay() {
            display.value = currentValue;
        }

        // Supporto tastiera
        calcModal.addEventListener('keydown', function(e) {
            if (e.key >= '0' && e.key <= '9') {
                handleCalcInput(e.key);
            } else if (['+', '-', '*', '/'].includes(e.key)) {
                handleCalcInput(e.key);
            } else if (e.key === 'Enter' || e.key === '=') {
                handleCalcInput('=');
            } else if (e.key === 'Escape' || e.key === 'c' || e.key === 'C') {
                handleCalcInput('C');
            } else if (e.key === '.') {
                handleCalcInput('.');
            }
        });
    }

    // ========================================================================
    // CALENDARIO
    // ========================================================================
    function initCalendario() {
        const calendarioBtn = document.getElementById('calendarioBtn');
        const calendarioModal = document.getElementById('calendarioModal');

        if (!calendarioBtn || !calendarioModal) return;

        const modal = new bootstrap.Modal(calendarioModal);

        calendarioBtn.addEventListener('click', function(e) {
            e.preventDefault();
            modal.show();
        });

        // TODO: Implementare calendario vero con FullCalendar.js o simile
        // Per ora mostra solo messaggio placeholder
    }

    // ========================================================================
    // PROFILO LINK
    // ========================================================================
    function initProfiloLink() {
        const profiloLink = document.getElementById('profiloLink');

        if (!profiloLink) return;

        profiloLink.addEventListener('click', function(e) {
            e.preventDefault();

            // Mostra alert temporaneo (sostituire con pagina profilo reale)
            alert('Pagina profilo utente in sviluppo.\n\nSarà disponibile con l\'app dipendenti.');
        });
    }

    // ========================================================================
    // DATA E ORA CORRENTE
    // ========================================================================
    function initDateTime() {
        const dateTimeEl = document.getElementById('currentDateTime');

        if (!dateTimeEl) return;

        function updateDateTime() {
            const now = new Date();
            const options = {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            };
            dateTimeEl.textContent = now.toLocaleDateString('it-IT', options);
        }

        // Aggiorna subito
        updateDateTime();

        // Aggiorna ogni minuto
        setInterval(updateDateTime, 60000);
    }

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================

    /**
     * Mostra un toast di notifica
     */
    window.showToast = function(message, type = 'success') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    };

    /**
     * Conferma azione con dialog
     */
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };

})();
