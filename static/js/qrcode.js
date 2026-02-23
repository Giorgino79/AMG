/**
 * Sistema di gestione QR Code - ModularBEF
 * Gestisce generazione, visualizzazione e download di QR Code per oggetti
 * VERSION: 2026-01-16-v1
 */

console.log('QRCode.js VERSION: 2026-01-16-v1 loaded');

(function() {
    'use strict';

    // ========================================================================
    // VARIABILI GLOBALI
    // ========================================================================
    let currentContentType = null;
    let currentObjectId = null;
    let currentQRCodeId = null;

    // ========================================================================
    // INIZIALIZZAZIONE
    // ========================================================================
    document.addEventListener('DOMContentLoaded', function() {
        initQRCodeButton();
        checkExistingQRCode();
    });

    // ========================================================================
    // INIZIALIZZAZIONE BOTTONE
    // ========================================================================
    function initQRCodeButton() {
        const btnGenerate = document.getElementById('btnGenerateQRCode');
        if (!btnGenerate) return;

        currentContentType = btnGenerate.getAttribute('data-content-type');
        currentObjectId = btnGenerate.getAttribute('data-object-id');

        console.log('QRCode button initialized:', {currentContentType, currentObjectId});

        btnGenerate.addEventListener('click', generateOrShowQRCode);
    }

    // ========================================================================
    // VERIFICA QR CODE ESISTENTE
    // ========================================================================
    function checkExistingQRCode() {
        if (!currentContentType || !currentObjectId) return;

        console.log('Checking for existing QR Code...');

        fetch(`/core/qrcode/check/?content_type=${currentContentType}&object_id=${currentObjectId}`)
            .then(response => response.json())
            .then(data => {
                console.log('QR Code check response:', data);
                if (data.success && data.exists) {
                    // QR Code esiste, mostra badge
                    currentQRCodeId = data.qrcode.id;
                    showQRCodeBadge(data.qrcode);
                }
            })
            .catch(error => {
                console.error('Errore verifica QR Code:', error);
            });
    }

    // ========================================================================
    // GENERA O MOSTRA QR CODE
    // ========================================================================
    function generateOrShowQRCode() {
        console.log('Generate or show QR Code clicked');

        // Apri modal
        const modal = new bootstrap.Modal(document.getElementById('qrCodeModal'));
        modal.show();

        // Mostra loading
        showElement('qrCodeLoading');
        hideElement('qrCodeContent');
        hideElement('qrCodeError');
        hideElement('qrCodeDownload');

        // Prepara FormData
        const formData = new FormData();
        formData.append('content_type', currentContentType);
        formData.append('object_id', currentObjectId);

        // AJAX per generare/recuperare QR Code
        fetch('/core/qrcode/generate/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('QR Code generate response:', data);
            hideElement('qrCodeLoading');

            if (data.success) {
                currentQRCodeId = data.qrcode.id;
                displayQRCode(data.qrcode);

                // Se è stato appena creato, mostra badge
                if (data.qrcode.created) {
                    showQRCodeBadge(data.qrcode);
                }
            } else {
                showQRCodeError(data.error || 'Errore nella generazione del QR Code');
            }
        })
        .catch(error => {
            console.error('Errore generazione QR Code:', error);
            hideElement('qrCodeLoading');
            showQRCodeError('Errore durante la generazione del QR Code');
        });
    }

    // ========================================================================
    // VISUALIZZA QR CODE
    // ========================================================================
    function displayQRCode(qrcode) {
        // Mostra immagine
        document.getElementById('qrCodeImage').src = qrcode.image_url;

        // Mostra URL
        document.getElementById('qrCodeUrl').textContent = qrcode.url;

        // Setup download button
        const downloadBtn = document.getElementById('qrCodeDownload');
        downloadBtn.href = `/core/qrcode/${qrcode.id}/download/`;

        showElement('qrCodeContent');
        showElement('qrCodeDownload');
    }

    function showQRCodeError(message) {
        const errorDiv = document.getElementById('qrCodeError');
        errorDiv.textContent = message;
        showElement('qrCodeError');
    }

    // ========================================================================
    // BADGE QR CODE NEL TITOLO
    // ========================================================================
    function showQRCodeBadge(qrcode) {
        const badge = document.getElementById('qrCodeBadge');
        const badgeLink = document.getElementById('qrCodeBadgeLink');

        if (!badge || !badgeLink) return;

        // Setup click handler per mostrare il QR Code
        badgeLink.addEventListener('click', function(e) {
            e.preventDefault();
            showExistingQRCode(qrcode);
        });

        // Mostra badge
        badge.classList.remove('d-none');
        console.log('QR Code badge shown');
    }

    function showExistingQRCode(qrcode) {
        console.log('Showing existing QR Code');

        // Apri modal
        const modal = new bootstrap.Modal(document.getElementById('qrCodeModal'));
        modal.show();

        // Nascondi loading e mostra direttamente il QR Code
        hideElement('qrCodeLoading');
        hideElement('qrCodeError');
        displayQRCode(qrcode);
    }

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================
    function showElement(elementId) {
        const el = document.getElementById(elementId);
        if (el) el.classList.remove('d-none');
    }

    function hideElement(elementId) {
        const el = document.getElementById(elementId);
        if (el) el.classList.add('d-none');
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

})();
