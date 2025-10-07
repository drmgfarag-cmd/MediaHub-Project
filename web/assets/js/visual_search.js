/**
 * Visual Search Module for MediaHub
 * Provides image-based content discovery interface
 */

class VisualSearch {
  constructor() {
    this.currentSearchId = null;
    this.uploadedImage = null;
  }

  /**
   * Initialize visual search interface
   */
  init() {
    this.createUploadModal();
    this.attachEventListeners();
  }

  /**
   * Create upload modal
   */
  createUploadModal() {
    if (document.getElementById('visualSearchModal')) return;

    const modal = document.createElement('div');
    modal.id = 'visualSearchModal';
    modal.className = 'modal-backdrop';
    modal.style.display = 'none';
    modal.innerHTML = `
      <div class="modal" role="dialog" aria-labelledby="visualSearchTitle" aria-modal="true">
        <div class="modal-header">
          <h2 class="modal-title" id="visualSearchTitle">Visual Search</h2>
          <button class="modal-close" aria-label="Close modal" onclick="visualSearch.closeModal()">✕</button>
        </div>
        <div class="modal-body">
          <div class="visual-search-container">
            <div class="upload-area" id="uploadArea">
              <div class="upload-icon">🖼️</div>
              <p class="upload-text">Drag and drop an image here</p>
              <p class="upload-subtext">or</p>
              <button class="btn btn-primary" onclick="document.getElementById('imageFileInput').click()">
                Choose Image
              </button>
              <input type="file" id="imageFileInput" accept="image/*" style="display: none;">
              <p class="upload-hint">Supported formats: JPG, PNG, GIF, WebP</p>
            </div>
            
            <div class="image-preview" id="imagePreview" style="display: none;">
              <img id="previewImage" alt="Uploaded image preview">
              <div class="preview-actions">
                <button class="btn btn-secondary" onclick="visualSearch.clearImage()">Clear</button>
                <button class="btn btn-primary" onclick="visualSearch.searchByImage()">Search</button>
              </div>
            </div>
            
            <div class="search-results" id="visualSearchResults" style="display: none;">
              <h3>Search Results</h3>
              <div id="resultsContainer"></div>
            </div>
            
            <div class="loading-state" id="visualSearchLoading" style="display: none;">
              <div class="spinner"></div>
              <p>Analyzing image...</p>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('imageFileInput');

    if (!uploadArea || !fileInput) return;

    // File input change
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        this.handleImageFile(file);
      }
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('drag-over');
      
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        this.handleImageFile(file);
      } else {
        alert('Please drop an image file');
      }
    });

    // Paste support
    document.addEventListener('paste', (e) => {
      if (!document.getElementById('visualSearchModal').style.display === 'flex') return;
      
      const items = e.clipboardData.items;
      for (let item of items) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          this.handleImageFile(file);
          break;
        }
      }
    });
  }

  /**
   * Handle image file
   */
  handleImageFile(file) {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      this.uploadedImage = file;
      this.showImagePreview(e.target.result);
    };
    reader.readAsDataURL(file);
  }

  /**
   * Show image preview
   */
  showImagePreview(dataUrl) {
    const uploadArea = document.getElementById('uploadArea');
    const preview = document.getElementById('imagePreview');
    const previewImage = document.getElementById('previewImage');

    uploadArea.style.display = 'none';
    preview.style.display = 'block';
    previewImage.src = dataUrl;
  }

  /**
   * Clear image
   */
  clearImage() {
    const uploadArea = document.getElementById('uploadArea');
    const preview = document.getElementById('imagePreview');
    const results = document.getElementById('visualSearchResults');

    uploadArea.style.display = 'block';
    preview.style.display = 'none';
    results.style.display = 'none';

    this.uploadedImage = null;
    this.currentSearchId = null;
    document.getElementById('imageFileInput').value = '';
  }

  /**
   * Search by image
   */
  async searchByImage() {
    if (!this.uploadedImage) {
      alert('Please select an image first');
      return;
    }

    const loading = document.getElementById('visualSearchLoading');
    const preview = document.getElementById('imagePreview');
    
    loading.style.display = 'block';
    preview.style.display = 'none';

    try {
      // Upload image
      const formData = new FormData();
      formData.append('image', this.uploadedImage);

      const uploadResponse = await fetch('/api/search/visual/upload', {
        method: 'POST',
        body: formData
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload image');
      }

      const uploadData = await uploadResponse.json();
      this.currentSearchId = uploadData.search_id;

      // Search for similar content
      const searchResponse = await fetch('/api/search/visual/find', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          search_id: this.currentSearchId
        })
      });

      if (!searchResponse.ok) {
        throw new Error('Search failed');
      }

      const searchData = await searchResponse.json();
      this.displayResults(searchData.results);

    } catch (error) {
      console.error('Visual search error:', error);
      alert(`Error: ${error.message}`);
      preview.style.display = 'block';
    } finally {
      loading.style.display = 'none';
    }
  }

  /**
   * Display search results
   */
  displayResults(results) {
    const resultsDiv = document.getElementById('visualSearchResults');
    const container = document.getElementById('resultsContainer');

    if (!results || (!results.matches.length && !results.suggestions.length)) {
      container.innerHTML = '<p class="text-secondary">No similar content found</p>';
    } else {
      const allResults = [...results.matches, ...results.suggestions];
      container.innerHTML = allResults.map(item => `
        <div class="search-result-item">
          <div class="result-info">
            <h4>${item.title}</h4>
            <p class="text-secondary">${item.type} • ${Math.round(item.similarity * 100)}% match</p>
            <p class="text-sm">${item.match_reason || ''}</p>
          </div>
          <button class="btn btn-sm btn-primary" onclick="window.location.href='/${item.type}s.html?id=${item.id}'">
            View
          </button>
        </div>
      `).join('');
    }

    resultsDiv.style.display = 'block';
  }

  /**
   * Open modal
   */
  openModal() {
    const modal = document.getElementById('visualSearchModal');
    if (modal) {
      modal.style.display = 'flex';
      this.clearImage();
    }
  }

  /**
   * Close modal
   */
  closeModal() {
    const modal = document.getElementById('visualSearchModal');
    if (modal) {
      modal.style.display = 'none';
      this.clearImage();
    }
  }
}

// Global instance
const visualSearch = new VisualSearch();

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => visualSearch.init());
} else {
  visualSearch.init();
}
