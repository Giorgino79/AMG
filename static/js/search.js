/**
 * Sistema di ricerca globale - ModularBEF
 * Gestisce autocomplete e navigazione risultati
 */

(function() {
    'use strict';

    // ========================================================================
    // VARIABILI GLOBALI
    // ========================================================================
    let searchTimeout = null;
    const SEARCH_DELAY = 300; // ms
    const MIN_QUERY_LENGTH = 2;

    // ========================================================================
    // INIZIALIZZAZIONE
    // ========================================================================
    document.addEventListener('DOMContentLoaded', function() {
        initGlobalSearch();
        initMobileSearch();
    });

    // ========================================================================
    // RICERCA GLOBALE
    // ========================================================================
    function initGlobalSearch() {
        const searchInput = document.getElementById('globalSearch');
        const searchDropdown = document.getElementById('searchResultsDropdown');

        if (!searchInput || !searchDropdown) return;

        // Event listener input con debounce
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();

            // Cancella timeout precedente
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }

            // Nascondi dropdown se query troppo corta
            if (query.length < MIN_QUERY_LENGTH) {
                hideSearchDropdown();
                return;
            }

            // Mostra loading
            showSearchLoading();

            // Debounce: attendi SEARCH_DELAY ms prima di cercare
            searchTimeout = setTimeout(function() {
                performSearch(query);
            }, SEARCH_DELAY);
        });

        // Chiudi dropdown quando si clicca fuori
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                hideSearchDropdown();
            }
        });

        // Gestione tasti freccia e Enter
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideSearchDropdown();
                searchInput.blur();
            }
        });
    }

    function performSearch(query) {
        fetch(`/core/search/?q=${encodeURIComponent(query)}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            hideSearchLoading();

            if (data.success && data.results && data.results.length > 0) {
                renderSearchResults(data.results);
                showSearchDropdown();
            } else {
                showNoResults();
            }
        })
        .catch(error => {
            console.error('Errore ricerca:', error);
            hideSearchLoading();
            showSearchError();
        });
    }

    function renderSearchResults(results) {
        const container = document.getElementById('searchResultsContainer');
        container.innerHTML = '';

        // Itera categorie
        results.forEach(category => {
            // Header categoria
            const categoryHeader = document.createElement('div');
            categoryHeader.className = 'search-results-category';
            categoryHeader.textContent = category.category;
            container.appendChild(categoryHeader);

            // Items categoria
            category.items.forEach(item => {
                const resultItem = createResultItem(item);
                container.appendChild(resultItem);
            });
        });
    }

    function createResultItem(item) {
        const link = document.createElement('a');
        link.href = item.url;
        link.className = 'search-result-item';

        link.innerHTML = `
            <div class="result-icon">
                <i class="${item.icon}"></i>
            </div>
            <div class="result-content">
                <div class="result-title">${escapeHtml(item.title)}</div>
                <div class="result-subtitle">${escapeHtml(item.subtitle)}</div>
            </div>
        `;

        // Nascondi dropdown al click
        link.addEventListener('click', function() {
            hideSearchDropdown();
        });

        return link;
    }

    // ========================================================================
    // UI HELPERS
    // ========================================================================
    function showSearchDropdown() {
        const dropdown = document.getElementById('searchResultsDropdown');
        dropdown.classList.remove('d-none');
        document.getElementById('searchResultsContainer').classList.remove('d-none');
        document.getElementById('searchNoResults').classList.add('d-none');
    }

    function hideSearchDropdown() {
        const dropdown = document.getElementById('searchResultsDropdown');
        dropdown.classList.add('d-none');
    }

    function showSearchLoading() {
        const dropdown = document.getElementById('searchResultsDropdown');
        const loading = document.getElementById('searchLoading');

        dropdown.classList.remove('d-none');
        loading.classList.remove('d-none');
        document.getElementById('searchResultsContainer').classList.add('d-none');
        document.getElementById('searchNoResults').classList.add('d-none');
    }

    function hideSearchLoading() {
        document.getElementById('searchLoading').classList.add('d-none');
    }

    function showNoResults() {
        const dropdown = document.getElementById('searchResultsDropdown');
        const noResults = document.getElementById('searchNoResults');

        dropdown.classList.remove('d-none');
        noResults.classList.remove('d-none');
        document.getElementById('searchResultsContainer').classList.add('d-none');
    }

    function showSearchError() {
        const dropdown = document.getElementById('searchResultsDropdown');
        const container = document.getElementById('searchResultsContainer');

        container.innerHTML = `
            <div class="text-center p-3 text-danger">
                <i class="bi bi-exclamation-triangle fs-4 d-block mb-2"></i>
                Errore durante la ricerca. Riprova.
            </div>
        `;

        dropdown.classList.remove('d-none');
        container.classList.remove('d-none');
        document.getElementById('searchNoResults').classList.add('d-none');
    }

    // ========================================================================
    // RICERCA MOBILE
    // ========================================================================
    function initMobileSearch() {
        const panel = document.getElementById('mobileSearchPanel');
        const toggle = document.getElementById('mobileSearchToggle');
        const closeBtn = document.getElementById('closeMobileSearch');
        const searchInput = document.getElementById('globalSearchMobile');
        const searchDropdown = document.getElementById('searchResultsDropdownMobile');

        if (!toggle || !panel) return;

        // Apri pannello al click sulla lente
        toggle.addEventListener('click', function() {
            panel.classList.toggle('d-none');
            if (!panel.classList.contains('d-none') && searchInput) {
                searchInput.focus();
            }
        });

        // Chiudi pannello al click su X
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                panel.classList.add('d-none');
                if (searchInput) searchInput.value = '';
                hideMobileDropdown();
            });
        }

        if (!searchInput || !searchDropdown) return;

        let mobileTimeout = null;

        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            if (mobileTimeout) clearTimeout(mobileTimeout);
            if (query.length < MIN_QUERY_LENGTH) {
                hideMobileDropdown();
                return;
            }
            showMobileLoading();
            mobileTimeout = setTimeout(function() {
                performMobileSearch(query);
            }, SEARCH_DELAY);
        });

        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                panel.classList.add('d-none');
                hideMobileDropdown();
            }
        });

        document.addEventListener('click', function(e) {
            if (!panel.contains(e.target) && e.target !== toggle) {
                panel.classList.add('d-none');
                hideMobileDropdown();
            }
        });
    }

    function performMobileSearch(query) {
        fetch(`/core/search/?q=${encodeURIComponent(query)}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            hideMobileLoading();
            if (data.success && data.results && data.results.length > 0) {
                renderMobileResults(data.results);
                showMobileDropdown();
            } else {
                showMobileNoResults();
            }
        })
        .catch(error => {
            console.error('Errore ricerca mobile:', error);
            hideMobileLoading();
        });
    }

    function renderMobileResults(results) {
        const container = document.getElementById('searchResultsContainerMobile');
        container.innerHTML = '';
        results.forEach(category => {
            const header = document.createElement('div');
            header.className = 'search-results-category';
            header.textContent = category.category;
            container.appendChild(header);
            category.items.forEach(item => {
                const link = createResultItem(item);
                link.addEventListener('click', hideMobileDropdown);
                container.appendChild(link);
            });
        });
    }

    function showMobileDropdown() {
        document.getElementById('searchResultsDropdownMobile').classList.remove('d-none');
        document.getElementById('searchResultsContainerMobile').classList.remove('d-none');
        document.getElementById('searchNoResultsMobile').classList.add('d-none');
    }

    function hideMobileDropdown() {
        const dd = document.getElementById('searchResultsDropdownMobile');
        if (dd) dd.classList.add('d-none');
    }

    function showMobileLoading() {
        document.getElementById('searchResultsDropdownMobile').classList.remove('d-none');
        document.getElementById('searchLoadingMobile').classList.remove('d-none');
        document.getElementById('searchResultsContainerMobile').classList.add('d-none');
        document.getElementById('searchNoResultsMobile').classList.add('d-none');
    }

    function hideMobileLoading() {
        document.getElementById('searchLoadingMobile').classList.add('d-none');
    }

    function showMobileNoResults() {
        document.getElementById('searchResultsDropdownMobile').classList.remove('d-none');
        document.getElementById('searchNoResultsMobile').classList.remove('d-none');
        document.getElementById('searchResultsContainerMobile').classList.add('d-none');
    }

    // ========================================================================
    // UTILITY FUNCTIONS
    // ========================================================================
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

})();
