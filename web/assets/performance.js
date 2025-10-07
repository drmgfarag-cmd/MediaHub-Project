// Performance Optimizations - MediaHub v5.7

// Lazy Loading Images
class LazyLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: options.rootMargin || '50px',
      threshold: options.threshold || 0.01,
      loadingClass: options.loadingClass || 'lazy-loading',
      loadedClass: options.loadedClass || 'lazy-loaded',
      ...options
    };

    this.observer = null;
    this.init();
  }

  init() {
    // Check for IntersectionObserver support
    if (!('IntersectionObserver' in window)) {
      this.loadAllImages();
      return;
    }

    this.observer = new IntersectionObserver(
      this.onIntersection.bind(this),
      {
        rootMargin: this.options.rootMargin,
        threshold: this.options.threshold
      }
    );

    this.observeImages();
  }

  observeImages() {
    const images = document.querySelectorAll('img[data-src], img[data-srcset]');
    images.forEach(img => this.observer.observe(img));
  }

  onIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.loadImage(entry.target);
        this.observer.unobserve(entry.target);
      }
    });
  }

  loadImage(img) {
    img.classList.add(this.options.loadingClass);

    const src = img.dataset.src;
    const srcset = img.dataset.srcset;

    if (srcset) {
      img.srcset = srcset;
    }
    if (src) {
      img.src = src;
    }

    img.addEventListener('load', () => {
      img.classList.remove(this.options.loadingClass);
      img.classList.add(this.options.loadedClass);
      delete img.dataset.src;
      delete img.dataset.srcset;
    }, { once: true });

    img.addEventListener('error', () => {
      img.classList.remove(this.options.loadingClass);
      console.error('Failed to load image:', src || srcset);
    }, { once: true });
  }

  loadAllImages() {
    const images = document.querySelectorAll('img[data-src], img[data-srcset]');
    images.forEach(img => this.loadImage(img));
  }

  refresh() {
    if (this.observer) {
      this.observeImages();
    }
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// Virtual Scrolling for Large Lists
class VirtualScroller {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.options = {
      itemHeight: options.itemHeight || 100,
      buffer: options.buffer || 5,
      renderItem: options.renderItem || ((item) => `<div>${JSON.stringify(item)}</div>`),
      ...options
    };

    this.items = [];
    this.visibleStart = 0;
    this.visibleEnd = 0;
    this.scrollTop = 0;

    this.init();
  }

  init() {
    this.container.style.overflowY = 'auto';
    this.container.style.position = 'relative';

    this.viewport = document.createElement('div');
    this.viewport.style.position = 'relative';
    this.container.appendChild(this.viewport);

    this.container.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
  }

  setItems(items) {
    this.items = items;
    this.viewport.style.height = `${items.length * this.options.itemHeight}px`;
    this.render();
  }

  onScroll() {
    this.scrollTop = this.container.scrollTop;
    this.render();
  }

  render() {
    const containerHeight = this.container.clientHeight;
    const visibleStart = Math.floor(this.scrollTop / this.options.itemHeight);
    const visibleEnd = Math.ceil((this.scrollTop + containerHeight) / this.options.itemHeight);

    // Add buffer
    this.visibleStart = Math.max(0, visibleStart - this.options.buffer);
    this.visibleEnd = Math.min(this.items.length, visibleEnd + this.options.buffer);

    // Clear viewport
    this.viewport.innerHTML = '';

    // Render visible items
    for (let i = this.visibleStart; i < this.visibleEnd; i++) {
      const item = this.items[i];
      const element = document.createElement('div');
      element.style.position = 'absolute';
      element.style.top = `${i * this.options.itemHeight}px`;
      element.style.height = `${this.options.itemHeight}px`;
      element.style.width = '100%';
      element.innerHTML = this.options.renderItem(item, i);
      this.viewport.appendChild(element);
    }
  }
}

// Debounce and Throttle Utilities
function debounce(func, wait = 300) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function throttle(func, limit = 100) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Preload Critical Resources
class ResourcePreloader {
  constructor() {
    this.preloadedResources = new Set();
  }

  preloadImage(url) {
    if (this.preloadedResources.has(url)) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        this.preloadedResources.add(url);
        resolve();
      };
      img.onerror = reject;
      img.src = url;
    });
  }

  preloadImages(urls) {
    return Promise.all(urls.map(url => this.preloadImage(url)));
  }

  preloadScript(url) {
    if (this.preloadedResources.has(url)) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = url;
      script.onload = () => {
        this.preloadedResources.add(url);
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  preloadStylesheet(url) {
    if (this.preloadedResources.has(url)) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = url;
      link.onload = () => {
        this.preloadedResources.add(url);
        resolve();
      };
      link.onerror = reject;
      document.head.appendChild(link);
    });
  }
}

// Request Idle Callback Polyfill
window.requestIdleCallback = window.requestIdleCallback || function(cb) {
  const start = Date.now();
  return setTimeout(() => {
    cb({
      didTimeout: false,
      timeRemaining: () => Math.max(0, 50 - (Date.now() - start))
    });
  }, 1);
};

window.cancelIdleCallback = window.cancelIdleCallback || function(id) {
  clearTimeout(id);
};

// Batch DOM Updates
class DOMBatcher {
  constructor() {
    this.readQueue = [];
    this.writeQueue = [];
    this.scheduled = false;
  }

  read(callback) {
    this.readQueue.push(callback);
    this.schedule();
  }

  write(callback) {
    this.writeQueue.push(callback);
    this.schedule();
  }

  schedule() {
    if (this.scheduled) return;
    this.scheduled = true;

    requestAnimationFrame(() => {
      // Execute all reads first
      while (this.readQueue.length) {
        const callback = this.readQueue.shift();
        callback();
      }

      // Then execute all writes
      while (this.writeQueue.length) {
        const callback = this.writeQueue.shift();
        callback();
      }

      this.scheduled = false;
    });
  }
}

// Memory Management
class MemoryManager {
  constructor() {
    this.cache = new Map();
    this.maxSize = 50; // Maximum cache entries
  }

  set(key, value) {
    if (this.cache.size >= this.maxSize) {
      // Remove oldest entry
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
    this.cache.set(key, value);
  }

  get(key) {
    return this.cache.get(key);
  }

  has(key) {
    return this.cache.has(key);
  }

  clear() {
    this.cache.clear();
  }

  getSize() {
    return this.cache.size;
  }
}

// Export utilities
window.LazyLoader = LazyLoader;
window.VirtualScroller = VirtualScroller;
window.debounce = debounce;
window.throttle = throttle;
window.ResourcePreloader = ResourcePreloader;
window.DOMBatcher = DOMBatcher;
window.MemoryManager = MemoryManager;

// Auto-initialize lazy loading
document.addEventListener('DOMContentLoaded', () => {
  if (!window.lazyLoader) {
    window.lazyLoader = new LazyLoader();
  }

  if (!window.resourcePreloader) {
    window.resourcePreloader = new ResourcePreloader();
  }

  if (!window.domBatcher) {
    window.domBatcher = new DOMBatcher();
  }

  if (!window.memoryManager) {
    window.memoryManager = new MemoryManager();
  }
});
