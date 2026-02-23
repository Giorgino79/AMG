/**
 * Sistema di gestione allegati - ModularBEF
 * Gestisce upload, visualizzazione, eliminazione con permessi granulari
 * VERSION: 2026-01-16-v3
 */

console.log('Allegati.js VERSION: 2026-01-16-v3 loaded');

(function() {
    'use strict';

    // ========================================================================
    // VARIABILI GLOBALI
    // ========================================================================
    let currentContentType = null;
    let currentObjectId = null;
    let currentObjectName = null;
    let isUploading = false;  // Prevent double submit

    // ========================================================================
    // INIZIALIZZAZIONE
    // ========================================================================
    document.addEventListener('DOMContentLoaded', function() {
        initUploadModal();
        initGestioneModal();
    });

    // ========================================================================
    // UPLOAD MODAL
    // ========================================================================
    function initUploadModal() {
        const uploadModal = document.getElementById('allegatoUploadModal');
        if (!uploadModal) return;

        // Prevent multiple event listener registration
        if (uploadModal.dataset.initialized) return;
        uploadModal.dataset.initialized = 'true';

        // Quando si apre il modal, cattura content_type e object_id
        uploadModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            currentContentType = button.getAttribute('data-content-type');
            currentObjectId = button.getAttribute('data-object-id');
            currentObjectName = button.getAttribute('data-object-name');

            document.getElementById('upload_content_type').value = currentContentType;
            document.getElementById('upload_object_id').value = currentObjectId;

            // Update modal title with object info
            const objectInfo = document.getElementById('uploadModalObjectInfo');
            console.log('Upload Modal - ObjectName:', currentObjectName, 'ObjectId:', currentObjectId);
            if (objectInfo && currentObjectName) {
                objectInfo.textContent = `ID: ${currentObjectId} - ${currentObjectName}`;
                console.log('Upload Modal title updated:', objectInfo.textContent);
            } else {
                console.warn('Upload Modal - Missing element or data:', {objectInfo, currentObjectName});
            }

            // Reset form
            document.getElementById('allegatoUploadForm').reset();
            hideElement('uploadProgress');
            hideElement('uploadErrors');
        });

        // Gestione submit upload
        const uploadForm = document.getElementById('allegatoUploadForm');
        if (uploadForm && !uploadForm.dataset.initialized) {
            uploadForm.dataset.initialized = 'true';
            uploadForm.addEventListener('submit', handleUploadSubmit);
        }
    }

    function handleUploadSubmit(e) {
        e.preventDefault();

        // Prevent double submit
        if (isUploading) {
            console.warn('Upload already in progress, ignoring duplicate submit');
            return false;
        }

        console.log('Starting upload...');
        const formData = new FormData(e.target);
        const submitBtn = document.getElementById('uploadSubmitBtn');
        const progressBar = document.getElementById('uploadProgressBar');

        // Disabilita bottone e mostra progress
        isUploading = true;
        submitBtn.disabled = true;
        showElement('uploadProgress');
        hideElement('uploadErrors');

        // AJAX Upload con progress
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = percentComplete + '%';
            }
        });

        xhr.addEventListener('load', function() {
            isUploading = false;
            submitBtn.disabled = false;
            hideElement('uploadProgress');
            progressBar.style.width = '0%';

            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    // Chiudi modal
                    bootstrap.Modal.getInstance(document.getElementById('allegatoUploadModal')).hide();

                    // Mostra messaggio successo
                    showSuccessMessage('Allegato caricato con successo!');

                    // Ricarica lista allegati se modal gestione è aperto
                    const gestioneModal = document.getElementById('allegatiGestioneModal');
                    if (gestioneModal.classList.contains('show')) {
                        loadAllegatiList(currentContentType, currentObjectId);
                    }

                    // Aggiorna contatore nella sidebar (se esiste)
                    updateAllegatiCount();
                }
            } else {
                const response = JSON.parse(xhr.responseText);
                showUploadError(response.error || 'Errore durante il caricamento');
            }
        });

        xhr.addEventListener('error', function() {
            isUploading = false;
            submitBtn.disabled = false;
            hideElement('uploadProgress');
            showUploadError('Errore di connessione');
        });

        xhr.open('POST', '/core/allegati/upload/');
        xhr.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
        xhr.send(formData);
    }

    function showUploadError(message) {
        const errorDiv = document.getElementById('uploadErrors');
        errorDiv.textContent = message;
        showElement('uploadErrors');
    }

    // ========================================================================
    // GESTIONE MODAL
    // ========================================================================
    function initGestioneModal() {
        const gestioneModal = document.getElementById('allegatiGestioneModal');
        if (!gestioneModal) return;

        // Prevent multiple event listener registration
        if (gestioneModal.dataset.initialized) return;
        gestioneModal.dataset.initialized = 'true';

        gestioneModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            currentContentType = button.getAttribute('data-content-type');
            currentObjectId = button.getAttribute('data-object-id');
            currentObjectName = button.getAttribute('data-object-name');

            // Update modal title with object info
            const objectInfo = document.getElementById('gestioneModalObjectInfo');
            console.log('Gestione Modal - ObjectName:', currentObjectName, 'ObjectId:', currentObjectId);
            if (objectInfo && currentObjectName) {
                objectInfo.textContent = `ID: ${currentObjectId} - ${currentObjectName}`;
                console.log('Gestione Modal title updated:', objectInfo.textContent);
            } else {
                console.warn('Gestione Modal - Missing element or data:', {objectInfo, currentObjectName});
            }

            // Carica lista allegati
            loadAllegatiList(currentContentType, currentObjectId);
        });
    }

    function loadAllegatiList(contentType, objectId) {
        console.log('loadAllegatiList called with:', {contentType, objectId});

        const loadingDiv = document.getElementById('allegatiLoading');
        const tableDiv = document.getElementById('allegatiTableContainer');
        const noDataDiv = document.getElementById('noAllegatiMessage');

        // Mostra loading
        showElement('allegatiLoading');
        hideElement('allegatiTableContainer');
        hideElement('noAllegatiMessage');

        const url = `/core/allegati/list/?content_type=${contentType}&object_id=${objectId}`;
        console.log('Fetching from URL:', url);

        // AJAX fetch allegati
        fetch(url, {
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            hideElement('allegatiLoading');

            if (data.success && data.allegati && data.allegati.length > 0) {
                console.log('Found', data.allegati.length, 'allegati');
                renderAllegatiTable(data.allegati);
                showElement('allegatiTableContainer');
            } else {
                console.warn('No allegati found or error:', data);
                showElement('noAllegatiMessage');
            }
        })
        .catch(error => {
            hideElement('allegatiLoading');
            console.error('Errore caricamento allegati:', error);
            showGestioneError('Errore durante il caricamento degli allegati');
        });
    }

    function renderAllegatiTable(allegati) {
        const tbody = document.getElementById('allegatiTableBody');
        const template = document.getElementById('allegatoRowTemplate');

        tbody.innerHTML = '';

        allegati.forEach(allegato => {
            const row = template.content.cloneNode(true);
            const tr = row.querySelector('tr');

            tr.setAttribute('data-allegato-id', allegato.id);

            // Icona tipo file
            const icon = getFileIcon(allegato);
            row.querySelector('.allegato-icon').innerHTML = icon;

            // Nome e descrizione
            row.querySelector('.allegato-nome span').textContent = allegato.nome;
            if (allegato.descrizione) {
                row.querySelector('.allegato-descrizione').textContent = allegato.descrizione;
            } else {
                row.querySelector('.allegato-descrizione').remove();
            }

            // Dimensione
            row.querySelector('.allegato-dimensione').textContent = allegato.dimensione;

            // Uploaded by
            row.querySelector('.allegato-uploaded-by').textContent = allegato.uploaded_by;

            // Data
            row.querySelector('.allegato-data').textContent = allegato.data;

            // Bottone visualizza
            const btnVisualizza = row.querySelector('.btn-visualizza');
            if (allegato.is_pdf || allegato.is_image) {
                btnVisualizza.addEventListener('click', () => previewAllegato(allegato));
            } else {
                btnVisualizza.disabled = true;
                btnVisualizza.title = 'Anteprima non disponibile';
            }

            // Bottone download
            row.querySelector('.btn-download').href = allegato.url;

            // Bottone elimina (visibile solo se can_delete)
            const btnElimina = row.querySelector('.btn-elimina');
            if (allegato.can_delete) {
                btnElimina.style.display = 'inline-block';
                btnElimina.addEventListener('click', () => deleteAllegato(allegato.id));
            }

            tbody.appendChild(row);
        });
    }

    function getFileIcon(allegato) {
        if (allegato.is_pdf) {
            return '<i class="bi bi-file-earmark-pdf-fill text-danger fs-4"></i>';
        } else if (allegato.is_image) {
            return '<i class="bi bi-file-earmark-image-fill text-primary fs-4"></i>';
        } else if (allegato.nome.endsWith('.doc') || allegato.nome.endsWith('.docx')) {
            return '<i class="bi bi-file-earmark-word-fill text-info fs-4"></i>';
        } else if (allegato.nome.endsWith('.xls') || allegato.nome.endsWith('.xlsx')) {
            return '<i class="bi bi-file-earmark-excel-fill text-success fs-4"></i>';
        } else if (allegato.nome.endsWith('.zip')) {
            return '<i class="bi bi-file-earmark-zip-fill text-warning fs-4"></i>';
        } else {
            return '<i class="bi bi-file-earmark-fill text-secondary fs-4"></i>';
        }
    }

    function showGestioneError(message) {
        const errorDiv = document.getElementById('gestioneAllegatiErrors');
        errorDiv.textContent = message;
        showElement('gestioneAllegatiErrors');
    }

    // ========================================================================
    // PREVIEW ALLEGATO
    // ========================================================================
    function previewAllegato(allegato) {
        const previewModal = new bootstrap.Modal(document.getElementById('allegatoPreviewModal'));
        const previewTitle = document.getElementById('allegatoPreviewTitle');
        const previewBody = document.getElementById('allegatoPreviewBody');
        const downloadLink = document.getElementById('allegatoPreviewDownload');

        previewTitle.innerHTML = `<i class="bi bi-eye"></i> ${allegato.nome}`;
        downloadLink.href = allegato.url;
        downloadLink.download = allegato.nome;

        if (allegato.is_pdf) {
            previewBody.innerHTML = `
                <iframe src="${allegato.url}"
                        style="width: 100%; height: 500px; border: none;">
                </iframe>
            `;
        } else if (allegato.is_image) {
            previewBody.innerHTML = `
                <img src="${allegato.url}"
                     class="img-fluid"
                     alt="${allegato.nome}">
            `;
        }

        previewModal.show();
    }

    // ========================================================================
    // ELIMINA ALLEGATO
    // ========================================================================
    function deleteAllegato(allegatoId) {
        if (!confirm('Sei sicuro di voler eliminare questo allegato?')) {
            return;
        }

        fetch(`/core/allegati/${allegatoId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage('Allegato eliminato con successo');
                loadAllegatiList(currentContentType, currentObjectId);
                updateAllegatiCount();
            } else {
                alert('Errore: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Errore eliminazione:', error);
            alert('Errore durante l\'eliminazione');
        });
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

    function showSuccessMessage(message) {
        // Crea toast Bootstrap o alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3';
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    function updateAllegatiCount() {
        // Ricarica la pagina per aggiornare i contatori
        // Oppure implementare update via AJAX se necessario
        location.reload();
    }

})();
