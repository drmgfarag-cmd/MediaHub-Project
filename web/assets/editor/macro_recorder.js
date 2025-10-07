/**
 * Macro Recorder for MediaHub Text Editor
 * Records and replays sequences of editor actions
 */

class MacroRecorder {
  constructor(editorInstance) {
    this.editor = editorInstance;
    this.isRecording = false;
    this.isPlaying = false;
    this.currentMacro = [];
    this.savedMacros = this.loadSavedMacros();
    this.startPosition = null;
  }

  /**
   * Load saved macros from localStorage
   */
  loadSavedMacros() {
    try {
      const saved = localStorage.getItem('mediahub_editor_macros');
      return saved ? JSON.parse(saved) : {};
    } catch (error) {
      console.error('Error loading macros:', error);
      return {};
    }
  }

  /**
   * Save macros to localStorage
   */
  saveMacrosToStorage() {
    try {
      localStorage.setItem('mediahub_editor_macros', JSON.stringify(this.savedMacros));
    } catch (error) {
      console.error('Error saving macros:', error);
    }
  }

  /**
   * Start recording a macro
   */
  startRecording() {
    if (this.isRecording) return false;

    this.isRecording = true;
    this.currentMacro = [];
    this.startPosition = this.editor.getPosition();

    // Listen to editor changes
    this.disposables = [];
    
    // Record content changes
    this.disposables.push(
      this.editor.onDidChangeModelContent((e) => {
        if (this.isRecording && !this.isPlaying) {
          e.changes.forEach(change => {
            this.currentMacro.push({
              type: 'edit',
              timestamp: Date.now(),
              range: change.range,
              text: change.text,
              rangeLength: change.rangeLength
            });
          });
        }
      })
    );

    // Record cursor position changes
    this.disposables.push(
      this.editor.onDidChangeCursorPosition((e) => {
        if (this.isRecording && !this.isPlaying) {
          this.currentMacro.push({
            type: 'cursor',
            timestamp: Date.now(),
            position: e.position,
            reason: e.reason
          });
        }
      })
    );

    // Record selection changes
    this.disposables.push(
      this.editor.onDidChangeCursorSelection((e) => {
        if (this.isRecording && !this.isPlaying) {
          this.currentMacro.push({
            type: 'selection',
            timestamp: Date.now(),
            selection: e.selection
          });
        }
      })
    );

    this.updateUI('recording');
    return true;
  }

  /**
   * Stop recording
   */
  stopRecording() {
    if (!this.isRecording) return null;

    this.isRecording = false;

    // Dispose event listeners
    if (this.disposables) {
      this.disposables.forEach(d => d.dispose());
      this.disposables = [];
    }

    this.updateUI('idle');

    // Return the recorded macro
    return {
      actions: this.currentMacro,
      startPosition: this.startPosition,
      recordedAt: new Date().toISOString(),
      actionCount: this.currentMacro.length
    };
  }

  /**
   * Play a macro
   */
  async playMacro(macro) {
    if (this.isPlaying || this.isRecording) return false;

    this.isPlaying = true;
    this.updateUI('playing');

    try {
      // Set initial position if available
      if (macro.startPosition) {
        this.editor.setPosition(macro.startPosition);
      }

      // Execute each action with a small delay
      for (const action of macro.actions) {
        await this.executeAction(action);
        await this.sleep(10); // Small delay between actions
      }

      this.updateUI('idle');
      return true;

    } catch (error) {
      console.error('Error playing macro:', error);
      this.updateUI('error');
      return false;

    } finally {
      this.isPlaying = false;
    }
  }

  /**
   * Execute a single macro action
   */
  async executeAction(action) {
    switch (action.type) {
      case 'edit':
        this.editor.executeEdits('macro', [{
          range: action.range,
          text: action.text
        }]);
        break;

      case 'cursor':
        this.editor.setPosition(action.position);
        break;

      case 'selection':
        this.editor.setSelection(action.selection);
        break;

      default:
        console.warn('Unknown action type:', action.type);
    }
  }

  /**
   * Save current macro
   */
  saveMacro(name, description = '') {
    if (!this.currentMacro || this.currentMacro.length === 0) {
      return false;
    }

    const macro = {
      name,
      description,
      actions: this.currentMacro,
      startPosition: this.startPosition,
      recordedAt: new Date().toISOString(),
      actionCount: this.currentMacro.length
    };

    this.savedMacros[name] = macro;
    this.saveMacrosToStorage();
    return true;
  }

  /**
   * Load and play a saved macro
   */
  async playSavedMacro(name) {
    const macro = this.savedMacros[name];
    if (!macro) {
      console.error('Macro not found:', name);
      return false;
    }

    return await this.playMacro(macro);
  }

  /**
   * Delete a saved macro
   */
  deleteMacro(name) {
    if (this.savedMacros[name]) {
      delete this.savedMacros[name];
      this.saveMacrosToStorage();
      return true;
    }
    return false;
  }

  /**
   * Get list of saved macros
   */
  getSavedMacros() {
    return Object.keys(this.savedMacros).map(name => ({
      name,
      description: this.savedMacros[name].description,
      actionCount: this.savedMacros[name].actionCount,
      recordedAt: this.savedMacros[name].recordedAt
    }));
  }

  /**
   * Export macro to JSON
   */
  exportMacro(name) {
    const macro = this.savedMacros[name];
    if (!macro) return null;

    return JSON.stringify(macro, null, 2);
  }

  /**
   * Import macro from JSON
   */
  importMacro(jsonString) {
    try {
      const macro = JSON.parse(jsonString);
      if (!macro.name || !macro.actions) {
        throw new Error('Invalid macro format');
      }

      this.savedMacros[macro.name] = macro;
      this.saveMacrosToStorage();
      return true;

    } catch (error) {
      console.error('Error importing macro:', error);
      return false;
    }
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Update UI based on state
   */
  updateUI(state) {
    const recordBtn = document.getElementById('macroRecordBtn');
    const stopBtn = document.getElementById('macroStopBtn');
    const playBtn = document.getElementById('macroPlayBtn');
    const indicator = document.getElementById('macroIndicator');

    if (!recordBtn) return;

    switch (state) {
      case 'recording':
        recordBtn.disabled = true;
        recordBtn.classList.add('recording');
        if (stopBtn) stopBtn.disabled = false;
        if (playBtn) playBtn.disabled = true;
        if (indicator) {
          indicator.style.display = 'inline';
          indicator.textContent = '⏺ Recording...';
          indicator.className = 'macro-indicator recording';
        }
        break;

      case 'playing':
        if (recordBtn) recordBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = true;
        if (playBtn) playBtn.disabled = true;
        if (indicator) {
          indicator.style.display = 'inline';
          indicator.textContent = '▶ Playing...';
          indicator.className = 'macro-indicator playing';
        }
        break;

      case 'error':
        if (recordBtn) recordBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (playBtn) playBtn.disabled = false;
        if (indicator) {
          indicator.style.display = 'inline';
          indicator.textContent = '✕ Error';
          indicator.className = 'macro-indicator error';
          setTimeout(() => indicator.style.display = 'none', 3000);
        }
        break;

      case 'idle':
      default:
        if (recordBtn) {
          recordBtn.disabled = false;
          recordBtn.classList.remove('recording');
        }
        if (stopBtn) stopBtn.disabled = true;
        if (playBtn) playBtn.disabled = false;
        if (indicator) indicator.style.display = 'none';
        break;
    }
  }

  /**
   * Toggle recording
   */
  toggleRecording() {
    if (this.isRecording) {
      return this.stopRecording();
    } else {
      return this.startRecording();
    }
  }
}

// Export for use in editor
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MacroRecorder;
}
