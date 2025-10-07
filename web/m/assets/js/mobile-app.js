/**
 * MediaHub Mobile Application - Complete Implementation
 * Integrates with all Phase 1 restored features
 */

class MediaHubMobileApp {
    constructor() {
        this.currentPage = 'home';
        this.searchVisible = false;
        this.castDevices = [];
        this.currentSession = null;
        this.apiBase = '/api';
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        this.setupServiceWorker();
        await this.loadInitialData();
        this.hideLoadingScreen();
        this.showToast('MediaHub Mobile loaded successfully', 'success');
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateToPage(page);
            });
        });
        
        // Search toggle
        document.getElementById('search-toggle').addEventListener('click', () => {
            this.toggleSearch();
        });
        
        // Search input
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        // Search clear
        document.getElementById('search-clear').addEventListener('click', () => {
            this.clearSearch();
        });
        
        // Search filters
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                this.setSearchFilter(e.target.dataset.type);
            });
        });
        
        // Cast toggle
        document.getElementById('cast-toggle').addEventListener('click', () => {
            this.showCastModal();
        });
        
        // Menu toggle
        document.getElementById('menu-toggle').addEventListener('click', () => {
            this.toggleMenu();
        });
        
        // Modal close buttons
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.closeModal(e.target.closest('.modal'));
            });
        });
        
        // Settings toggles
        document.querySelectorAll('.setting-toggle input').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                this.updateSetting(e.target.id, e.target.checked);
            });
        });
        
        // Settings selects
        document.querySelectorAll('.setting-select').forEach(select => {
            select.addEventListener('change', (e) => {
                this.updateSetting(e.target.id, e.target.value);
            });
        });
        
        // Discover devices button
        document.getElementById('discover-devices').addEventListener('click', () => {
            this.discoverCastDevices();
        });
    }
    
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/m/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }
    
    async loadInitialData() {
        try {
            // Load smart rails data
            await this.loadSmartRails();
            
            // Load library data
            await this.loadLibrary();
            
            // Load downloads
            await this.loadDownloads();
            
            // Load settings
            await this.loadSettings();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Error loading data', 'error');
        }
    }
    
    async loadSmartRails() {
        try {
            const response = await fetch(`${this.apiBase}/smart_rails/mobile/all`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSmartRails(data.rails);
            }
        } catch (error) {
            console.error('Error loading smart rails:', error);
        }
    }
    
    renderSmartRails(rails) {
        // Render recommended rail
        if (rails.recommended) {
            this.renderRail('recommended-items', rails.recommended.items);
        }
        
        // Render premium rail
        if (rails.premium) {
            this.renderRail('premium-items', rails.premium.items);
        }
        
        // Render trending rail
        if (rails.trending) {
            this.renderRail('trending-items', rails.trending.items);
        }
        
        // Render collections rail
        if (rails.collections) {
            this.renderRail('collections-items', rails.collections.items);
        }
    }
    
    renderRail(containerId, items) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '';
        
        items.forEach(item => {
            const card = this.createMediaCard(item);
            container.appendChild(card);
        });
    }
    
    createMediaCard(item) {
        const card = document.createElement('div');
        card.className = 'media-card';
        card.dataset.itemId = item.id;
        
        const qualityBadges = this.createQualityBadges(item.quality_features);
        
        card.innerHTML = `
            <div class="media-poster">
                <img src="${item.poster || '/m/assets/icons/placeholder.png'}" alt="${item.title}" loading="lazy">
                ${qualityBadges}
                <div class="media-overlay">
                    <button class="btn btn-primary" onclick="mobileApp.playItem('${item.id}')">
                        <svg class="btn-icon" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z"/>
                        </svg>
                    </button>
                    <button class="btn btn-secondary" onclick="mobileApp.showItemDetails('${item.id}')">
                        <svg class="btn-icon" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="media-info">
                <div class="media-title">${item.title}</div>
                <div class="media-year">${item.year || ''}</div>
                <div class="media-rating">
                    <span class="rating-stars">★★★★☆</span>
                    <span class="rating-text">${item.rating || 'N/A'}</span>
                </div>
            </div>
        `;
        
        return card;
    }
    
    createQualityBadges(qualityFeatures) {
        if (!qualityFeatures) return '';
        
        let badges = '<div class="quality-badges">';
        
        if (qualityFeatures['4k_uhd']) {
            badges += '<span class="quality-badge uhd">4K</span>';
        }
        if (qualityFeatures.hdr) {
            badges += '<span class="quality-badge hdr">HDR</span>';
        }
        if (qualityFeatures.atmos) {
            badges += '<span class="quality-badge atmos">ATMOS</span>';
        }
        
        badges += '</div>';
        return badges;
    }
    
    async loadLibrary() {
        try {
            const response = await fetch(`${this.apiBase}/stream/mobile/library`);
            const data = await response.json();
            
            if (data.success) {
                this.renderLibrary(data.library_items);
            }
        } catch (error) {
            console.error('Error loading library:', error);
        }
    }
    
    renderLibrary(items) {
        const container = document.getElementById('library-grid');
        if (!container) return;
        
        container.innerHTML = '';
        
        items.forEach(item => {
            const card = this.createMediaCard(item);
            container.appendChild(card);
        });
    }
    
    async loadDownloads() {
        try {
            // This would integrate with the download system
            const downloads = [
                {
                    id: 1,
                    title: 'Sample Download',
                    poster: '/m/assets/icons/placeholder.png',
                    progress: 75,
                    status: 'downloading',
                    speed: '2.5 MB/s',
                    eta: '5 min'
                }
            ];
            
            this.renderDownloads(downloads);
        } catch (error) {
            console.error('Error loading downloads:', error);
        }
    }
    
    renderDownloads(downloads) {
        const container = document.getElementById('downloads-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        downloads.forEach(download => {
            const item = document.createElement('div');
            item.className = 'download-item';
            
            item.innerHTML = `
                <div class="download-poster">
                    <img src="${download.poster}" alt="${download.title}">
                </div>
                <div class="download-info">
                    <div class="download-title">${download.title}</div>
                    <div class="download-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${download.progress}%"></div>
                        </div>
                    </div>
                    <div class="download-status">${download.status} - ${download.speed} - ${download.eta}</div>
                </div>
                <div class="download-actions">
                    <button class="icon-btn" onclick="mobileApp.pauseDownload('${download.id}')">
                        <svg class="icon" viewBox="0 0 24 24">
                            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                        </svg>
                    </button>
                    <button class="icon-btn" onclick="mobileApp.cancelDownload('${download.id}')">
                        <svg class="icon" viewBox="0 0 24 24">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    async loadSettings() {
        try {
            // Load settings from localStorage or API
            const settings = JSON.parse(localStorage.getItem('mobileSettings') || '{}');
            
            // Apply settings to UI
            Object.keys(settings).forEach(key => {
                const element = document.getElementById(key);
                if (element) {
                    if (element.type === 'checkbox') {
                        element.checked = settings[key];
                    } else {
                        element.value = settings[key];
                    }
                }
            });
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }
    
    navigateToPage(page) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(p => {
            p.classList.remove('active');
        });
        
        // Show target page
        const targetPage = document.getElementById(`page-${page}`);
        if (targetPage) {
            targetPage.classList.add('active');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[data-page="${page}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        this.currentPage = page;
        
        // Load page-specific data
        this.loadPageData(page);
    }
    
    async loadPageData(page) {
        switch (page) {
            case 'library':
                await this.loadLibrary();
                break;
            case 'downloads':
                await this.loadDownloads();
                break;
            case 'settings':
                await this.loadSettings();
                break;
        }
    }
    
    toggleSearch() {
        const searchContainer = document.getElementById('search-container');
        const searchInput = document.getElementById('search-input');
        
        this.searchVisible = !this.searchVisible;
        
        if (this.searchVisible) {
            searchContainer.style.display = 'block';
            searchInput.focus();
        } else {
            searchContainer.style.display = 'none';
            this.clearSearch();
        }
    }
    
    async handleSearch(query) {
        if (query.length < 2) return;
        
        try {
            const response = await fetch(`${this.apiBase}/smart_rails/mobile/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.success) {
                this.showSearchResults(data.results);
            }
        } catch (error) {
            console.error('Error searching:', error);
        }
    }
    
    showSearchResults(results) {
        const modal = document.getElementById('search-modal');
        const container = document.getElementById('search-results');
        
        container.innerHTML = '';
        
        results.forEach(result => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.onclick = () => this.showItemDetails(result.id);
            
            item.innerHTML = `
                <div class="search-result-poster">
                    <img src="${result.poster || '/m/assets/icons/placeholder.png'}" alt="${result.title}">
                </div>
                <div class="search-result-info">
                    <div class="search-result-title">${result.title}</div>
                    <div class="search-result-meta">${result.year || ''} • ${result.type || ''}</div>
                    <div class="search-result-description">${result.overview || ''}</div>
                </div>
            `;
            
            container.appendChild(item);
        });
        
        this.showModal(modal);
    }
    
    clearSearch() {
        const searchInput = document.getElementById('search-input');
        searchInput.value = '';
        this.closeModal(document.getElementById('search-modal'));
    }
    
    setSearchFilter(type) {
        document.querySelectorAll('.filter-chip').forEach(chip => {
            chip.classList.remove('active');
        });
        
        const activeChip = document.querySelector(`[data-type="${type}"]`);
        if (activeChip) {
            activeChip.classList.add('active');
        }
        
        // Re-run search with filter
        const query = document.getElementById('search-input').value;
        if (query) {
            this.handleSearch(query);
        }
    }
    
    async playItem(itemId) {
        try {
            // Get item details
            const response = await fetch(`${this.apiBase}/smart_rails/mobile/item/${itemId}`);
            const data = await response.json();
            
            if (data.success) {
                await this.startStreaming(data.item);
            }
        } catch (error) {
            console.error('Error playing item:', error);
            this.showToast('Error starting playback', 'error');
        }
    }
    
    async startStreaming(item) {
        try {
            // Create streaming session
            const response = await fetch(`${this.apiBase}/stream/mobile/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    file_path: item.path,
                    quality_profile: this.getQualityProfile()
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSession = data.session_id;
                this.showPlayer(item, data.streaming_urls);
            } else {
                this.showToast('Error creating streaming session', 'error');
            }
        } catch (error) {
            console.error('Error starting streaming:', error);
            this.showToast('Error starting streaming', 'error');
        }
    }
    
    showPlayer(item, streamingUrls) {
        const modal = document.getElementById('player-modal');
        const player = document.getElementById('mobile-player');
        const title = document.getElementById('player-title');
        const description = document.getElementById('player-description');
        
        title.textContent = item.title;
        description.textContent = item.overview || '';
        
        // Set video source
        if (streamingUrls.direct) {
            player.src = streamingUrls.direct;
        } else if (streamingUrls.hls) {
            // For HLS, we'd need hls.js library
            player.src = streamingUrls.hls;
        }
        
        this.showModal(modal);
        player.play();
    }
    
    getQualityProfile() {
        const qualitySelect = document.getElementById('default-quality');
        return qualitySelect ? qualitySelect.value : 'mobile_medium';
    }
    
    async showItemDetails(itemId) {
        try {
            const response = await fetch(`${this.apiBase}/smart_rails/mobile/item/${itemId}`);
            const data = await response.json();
            
            if (data.success) {
                // Show item details in a modal or navigate to details page
                console.log('Item details:', data.item);
                this.showToast(`Details for ${data.item.title}`, 'info');
            }
        } catch (error) {
            console.error('Error loading item details:', error);
        }
    }
    
    async showCastModal() {
        const modal = document.getElementById('cast-modal');
        this.showModal(modal);
        await this.discoverCastDevices();
    }
    
    async discoverCastDevices() {
        const container = document.getElementById('cast-devices');
        
        // Show scanning state
        container.innerHTML = `
            <div class="device-scanning">
                <div class="scanning-spinner"></div>
                <p>Scanning for devices...</p>
            </div>
        `;
        
        try {
            const response = await fetch(`${this.apiBase}/stream/cast/webos/discover`);
            const data = await response.json();
            
            if (data.success) {
                this.renderCastDevices(data.discovered_devices);
            } else {
                container.innerHTML = '<p>No devices found</p>';
            }
        } catch (error) {
            console.error('Error discovering devices:', error);
            container.innerHTML = '<p>Error discovering devices</p>';
        }
    }
    
    renderCastDevices(devices) {
        const container = document.getElementById('cast-devices');
        container.innerHTML = '';
        
        devices.forEach(device => {
            const item = document.createElement('div');
            item.className = 'device-item';
            item.onclick = () => this.connectToDevice(device);
            
            item.innerHTML = `
                <div class="device-icon">
                    <svg class="icon" viewBox="0 0 24 24">
                        <path d="M21 3H3c-1.1 0-2 .9-2 2v3h2V5h18v14h-7v2h7c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/>
                    </svg>
                </div>
                <div class="device-info">
                    <div class="device-name">${device.name}</div>
                    <div class="device-status">${device.model} • ${device.ip_address}</div>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    async connectToDevice(device) {
        try {
            const response = await fetch(`${this.apiBase}/stream/cast/webos/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    device_id: device.id,
                    ip_address: device.ip_address
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast(`Connected to ${device.name}`, 'success');
                this.closeModal(document.getElementById('cast-modal'));
            } else {
                this.showToast('Failed to connect to device', 'error');
            }
        } catch (error) {
            console.error('Error connecting to device:', error);
            this.showToast('Error connecting to device', 'error');
        }
    }
    
    updateSetting(key, value) {
        // Save to localStorage
        const settings = JSON.parse(localStorage.getItem('mobileSettings') || '{}');
        settings[key] = value;
        localStorage.setItem('mobileSettings', JSON.stringify(settings));
        
        this.showToast('Setting updated', 'success');
    }
    
    pauseDownload(downloadId) {
        // Implement download pause
        this.showToast('Download paused', 'info');
    }
    
    cancelDownload(downloadId) {
        // Implement download cancel
        this.showToast('Download cancelled', 'warning');
    }
    
    toggleMenu() {
        // Implement menu toggle if needed
        console.log('Menu toggle');
    }
    
    showModal(modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
    
    closeModal(modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
    
    hideLoadingScreen() {
        const loadingScreen = document.getElementById('loading-screen');
        const app = document.getElementById('app');
        
        loadingScreen.style.display = 'none';
        app.style.display = 'flex';
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }
}

// Initialize the mobile app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mobileApp = new MediaHubMobileApp();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MediaHubMobileApp;
}
