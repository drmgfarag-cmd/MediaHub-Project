/**
 * Voice Search Module for MediaHub
 * Provides speech-to-text search functionality using Web Speech API
 */

class VoiceSearch {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.onResultCallback = null;
    this.onErrorCallback = null;
    this.initRecognition();
  }

  /**
   * Initialize speech recognition
   */
  initRecognition() {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      console.warn('Speech recognition not supported in this browser');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.continuous = false;
    this.recognition.interimResults = true;
    this.recognition.lang = 'en-US'; // Default language

    // Event handlers
    this.recognition.onstart = () => {
      this.isListening = true;
      this.updateUI('listening');
    };

    this.recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      
      if (this.onResultCallback) {
        this.onResultCallback(transcript, event.results[0].isFinal);
      }
    };

    this.recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      this.isListening = false;
      this.updateUI('error');
      
      if (this.onErrorCallback) {
        this.onErrorCallback(event.error);
      }
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.updateUI('idle');
    };
  }

  /**
   * Check if voice search is supported
   */
  isSupported() {
    return this.recognition !== null;
  }

  /**
   * Start listening for voice input
   */
  startListening(onResult, onError) {
    if (!this.isSupported()) {
      const error = 'Voice search not supported in this browser';
      if (onError) onError(error);
      return false;
    }

    if (this.isListening) {
      return false;
    }

    this.onResultCallback = onResult;
    this.onErrorCallback = onError;

    try {
      this.recognition.start();
      return true;
    } catch (error) {
      console.error('Error starting voice recognition:', error);
      if (onError) onError(error.message);
      return false;
    }
  }

  /**
   * Stop listening
   */
  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }
  }

  /**
   * Set recognition language
   */
  setLanguage(lang) {
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }

  /**
   * Update UI based on state
   */
  updateUI(state) {
    const voiceBtn = document.getElementById('voiceSearchBtn');
    const voiceIndicator = document.getElementById('voiceSearchIndicator');
    
    if (!voiceBtn) return;

    switch (state) {
      case 'listening':
        voiceBtn.classList.add('listening');
        voiceBtn.innerHTML = '🎤';
        voiceBtn.title = 'Listening... Click to stop';
        if (voiceIndicator) {
          voiceIndicator.style.display = 'block';
          voiceIndicator.textContent = 'Listening...';
        }
        break;
      
      case 'processing':
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '⏳';
        voiceBtn.title = 'Processing...';
        if (voiceIndicator) {
          voiceIndicator.textContent = 'Processing...';
        }
        break;
      
      case 'error':
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '🎤';
        voiceBtn.title = 'Voice Search (Error occurred)';
        if (voiceIndicator) {
          voiceIndicator.style.display = 'none';
        }
        break;
      
      case 'idle':
      default:
        voiceBtn.classList.remove('listening');
        voiceBtn.innerHTML = '🎤';
        voiceBtn.title = 'Voice Search';
        if (voiceIndicator) {
          voiceIndicator.style.display = 'none';
        }
        break;
    }
  }

  /**
   * Toggle voice search on/off
   */
  toggle(onResult, onError) {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening(onResult, onError);
    }
  }
}

// Global instance
const voiceSearch = new VoiceSearch();

/**
 * Initialize voice search button
 */
function initVoiceSearchButton(searchInputId = 'searchInput') {
  const searchInput = document.getElementById(searchInputId);
  
  if (!searchInput) {
    console.warn('Search input not found for voice search');
    return;
  }

  // Create voice search button if it doesn't exist
  let voiceBtn = document.getElementById('voiceSearchBtn');
  if (!voiceBtn) {
    voiceBtn = document.createElement('button');
    voiceBtn.id = 'voiceSearchBtn';
    voiceBtn.className = 'btn btn-icon btn-ghost voice-search-btn';
    voiceBtn.innerHTML = '🎤';
    voiceBtn.title = 'Voice Search';
    voiceBtn.setAttribute('aria-label', 'Voice Search');
    
    // Insert after search input
    searchInput.parentNode.insertBefore(voiceBtn, searchInput.nextSibling);
  }

  // Create indicator
  let indicator = document.getElementById('voiceSearchIndicator');
  if (!indicator) {
    indicator = document.createElement('span');
    indicator.id = 'voiceSearchIndicator';
    indicator.className = 'voice-search-indicator';
    indicator.style.display = 'none';
    voiceBtn.parentNode.insertBefore(indicator, voiceBtn.nextSibling);
  }

  // Handle button click
  voiceBtn.onclick = () => {
    if (!voiceSearch.isSupported()) {
      alert('Voice search is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    voiceSearch.toggle(
      (transcript, isFinal) => {
        searchInput.value = transcript;
        
        if (isFinal) {
          voiceSearch.updateUI('processing');
          
          // Trigger search
          const searchEvent = new Event('input', { bubbles: true });
          searchInput.dispatchEvent(searchEvent);
          
          // Also trigger form submit if exists
          const form = searchInput.closest('form');
          if (form) {
            form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
          }
          
          setTimeout(() => voiceSearch.updateUI('idle'), 1000);
        }
      },
      (error) => {
        console.error('Voice search error:', error);
        alert(`Voice search error: ${error}`);
      }
    );
  };
}

// Auto-initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => initVoiceSearchButton());
} else {
  initVoiceSearchButton();
}
