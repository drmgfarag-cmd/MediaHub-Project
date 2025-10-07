// Continue Watching Component - MediaHub v5.5

class ContinueWatching {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Continue watching container #${containerId} not found`);
      return;
    }

    this.options = {
      maxItems: options.maxItems || 12,
      autoRefresh: options.autoRefresh !== false,
      refreshInterval: options.refreshInterval || 60000, // 1 minute
      ...options
    };

    this.items = [];
    this.refreshTimer = null;

    this.init();
  }

  async init() {
    await this.loadContinueWatching();
    this.render();
    
    if (this.options.autoRefresh) {
      this.startAutoRefresh();
    }
  }

  async loadContinueWatching() {
    try {
      const response = await fetch('/api/watch_history/recent?limit=' + this.options.maxItems);
      if (!response.ok) {
        this.items = this.getMockItems();
        return;
      }
      const data = await response.json();
      this.items = data.items || this.getMockItems();
    } catch (error) {
      console.warn('Failed to load continue watching, using mock data:', error);
      this.items = this.getMockItems();
    }
  }

  getMockItems() {
    return [
      {
        id: 1,
        title: 'Breaking Bad',
        type: 'tv',
        season: 3,
        episode: 7,
        episodeTitle: 'One Minute',
        thumbnail: '/api/placeholder/480/270?text=Breaking+Bad',
        progress: 45,
        duration: 47,
        lastWatched: '2 hours ago'
      },
      {
        id: 2,
        title: 'Inception',
        type: 'movie',
        thumbnail: '/api/placeholder/480/270?text=Inception',
        progress: 78,
        duration: 148,
        lastWatched: '1 day ago'
      },
      {
        id: 3,
        title: 'The Mandalorian',
        type: 'tv',
        season: 2,
        episode: 4,
        episodeTitle: 'The Siege',
        thumbnail: '/api/placeholder/480/270?text=Mandalorian',
        progress: 12,
        duration: 33,
        lastWatched: '3 days ago'
      }
    ];
  }

  render() {
    if (this.items.length === 0) {
      this.renderEmpty();
      return;
    }

    const html = `
      <div class="section-header">
        <h2 class="section-title">Continue Watching</h2>
        <a href="/watch_history.html" class="section-link">See All →</a>
      </div>
      <div class="continue-grid">
        ${this.items.map(item => this.renderCard(item)).join('')}
      </div>
    `;
    
    this.container.innerHTML = html;
    this.setupEventListeners();
  }

  renderCard(item) {
    const progressPercent = (item.progress / item.duration) * 100;
    const timeRemaining = this.formatTime(item.duration - item.progress);
    
    let subtitle = '';
    if (item.type === 'tv') {
      subtitle = `S${item.season}:E${item.episode}`;
      if (item.episodeTitle) {
        subtitle += ` - ${item.episodeTitle}`;
      }
    }

    return `
      <div class="continue-card" data-id="${item.id}" data-type="${item.type}">
        <div class="continue-thumbnail" style="background-image: url('${item.thumbnail}')">
          <button class="continue-remove-btn" onclick="continueWatching.remove(${item.id})" title="Remove from Continue Watching">
            ×
          </button>
          <div class="continue-overlay">
            <button class="continue-play-btn" onclick="continueWatching.play(${item.id}, '${item.type}')">
              ▶
            </button>
          </div>
          <div class="continue-progress-bar">
            <div class="continue-progress-fill" style="width: ${progressPercent}%"></div>
          </div>
        </div>
        <div class="continue-info">
          <h3 class="continue-title">${item.title}</h3>
          ${subtitle ? `<p class="continue-episode">${subtitle}</p>` : ''}
          <div class="continue-meta">
            <span class="continue-time">
              <span>⏱</span>
              <span>${timeRemaining} left</span>
            </span>
            <span>${item.lastWatched}</span>
          </div>
          <div class="continue-actions">
            <button class="continue-action-btn" onclick="continueWatching.play(${item.id}, '${item.type}')">
              Resume
            </button>
            <button class="continue-action-btn" onclick="continueWatching.restart(${item.id}, '${item.type}')">
              Restart
            </button>
          </div>
        </div>
      </div>
    `;
  }

  renderEmpty() {
    this.container.innerHTML = `
      <div class="section-header">
        <h2 class="section-title">Continue Watching</h2>
      </div>
      <div class="continue-empty">
        <div class="continue-empty-icon">📺</div>
        <div class="continue-empty-text">Nothing to continue watching</div>
        <div class="continue-empty-subtext">Start watching something to see it here</div>
      </div>
    `;
  }

  setupEventListeners() {
    // Card click (excluding buttons)
    this.container.querySelectorAll('.continue-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('button')) return;
        
        const id = parseInt(card.dataset.id);
        const type = card.dataset.type;
        this.play(id, type);
      });
    });
  }

  formatTime(minutes) {
    if (minutes < 60) {
      return `${Math.round(minutes)}m`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }

  async play(id, type) {
    console.log(`Playing ${type} with ID: ${id}`);
    
    try {
      // Update last watched timestamp
      await fetch('/api/watch_history/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, type, action: 'resume' })
      });
    } catch (error) {
      console.error('Failed to update watch history:', error);
    }
    
    // Navigate to player
    window.location.href = `/player.html?id=${id}&type=${type}&resume=true`;
  }

  async restart(id, type) {
    console.log(`Restarting ${type} with ID: ${id}`);
    
    try {
      // Reset progress
      await fetch('/api/watch_history/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, type })
      });
    } catch (error) {
      console.error('Failed to reset progress:', error);
    }
    
    // Navigate to player
    window.location.href = `/player.html?id=${id}&type=${type}`;
  }

  async remove(id) {
    if (!confirm('Remove this item from Continue Watching?')) {
      return;
    }

    try {
      await fetch(`/api/watch_history/${id}`, {
        method: 'DELETE'
      });
      
      // Remove from local array
      this.items = this.items.filter(item => item.id !== id);
      
      // Re-render
      this.render();
    } catch (error) {
      console.error('Failed to remove item:', error);
      alert('Failed to remove item');
    }
  }

  async refresh() {
    await this.loadContinueWatching();
    this.render();
  }

  startAutoRefresh() {
    this.stopAutoRefresh();
    this.refreshTimer = setInterval(() => {
      this.refresh();
    }, this.options.refreshInterval);
  }

  stopAutoRefresh() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  destroy() {
    this.stopAutoRefresh();
    this.container.innerHTML = '';
  }
}

// Global instance
let continueWatching;

// Auto-initialize if continue-watching element exists
document.addEventListener('DOMContentLoaded', () => {
  const continueWatchingElement = document.getElementById('continue-watching');
  if (continueWatchingElement) {
    continueWatching = new ContinueWatching('continue-watching');
  }
});
