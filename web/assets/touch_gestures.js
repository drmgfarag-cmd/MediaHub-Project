// Touch Gestures - MediaHub v5.6

class TouchGestures {
  constructor(element, options = {}) {
    this.element = element;
    this.options = {
      swipeThreshold: options.swipeThreshold || 50,
      swipeTimeout: options.swipeTimeout || 300,
      tapTimeout: options.tapTimeout || 200,
      doubleTapTimeout: options.doubleTapTimeout || 300,
      longPressTimeout: options.longPressTimeout || 500,
      ...options
    };

    this.touchStartX = 0;
    this.touchStartY = 0;
    this.touchEndX = 0;
    this.touchEndY = 0;
    this.touchStartTime = 0;
    this.lastTapTime = 0;
    this.longPressTimer = null;

    this.init();
  }

  init() {
    this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
    this.element.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    this.element.addEventListener('touchend', this.handleTouchEnd.bind(this));
    this.element.addEventListener('touchcancel', this.handleTouchCancel.bind(this));
  }

  handleTouchStart(e) {
    this.touchStartX = e.touches[0].clientX;
    this.touchStartY = e.touches[0].clientY;
    this.touchStartTime = Date.now();

    // Start long press timer
    this.longPressTimer = setTimeout(() => {
      this.onLongPress(e);
    }, this.options.longPressTimeout);

    // Trigger touchstart event
    this.triggerEvent('touchstart', {
      x: this.touchStartX,
      y: this.touchStartY
    });
  }

  handleTouchMove(e) {
    // Cancel long press if moved
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    this.touchEndX = e.touches[0].clientX;
    this.touchEndY = e.touches[0].clientY;

    const deltaX = this.touchEndX - this.touchStartX;
    const deltaY = this.touchEndY - this.touchStartY;

    // Trigger touchmove event
    this.triggerEvent('touchmove', {
      x: this.touchEndX,
      y: this.touchEndY,
      deltaX,
      deltaY
    });
  }

  handleTouchEnd(e) {
    // Cancel long press
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    this.touchEndX = e.changedTouches[0].clientX;
    this.touchEndY = e.changedTouches[0].clientY;

    const deltaX = this.touchEndX - this.touchStartX;
    const deltaY = this.touchEndY - this.touchStartY;
    const deltaTime = Date.now() - this.touchStartTime;

    // Detect swipe
    if (Math.abs(deltaX) > this.options.swipeThreshold || Math.abs(deltaY) > this.options.swipeThreshold) {
      if (deltaTime < this.options.swipeTimeout) {
        this.onSwipe(deltaX, deltaY);
      }
    } else {
      // Detect tap or double tap
      if (deltaTime < this.options.tapTimeout) {
        const now = Date.now();
        if (now - this.lastTapTime < this.options.doubleTapTimeout) {
          this.onDoubleTap(e);
          this.lastTapTime = 0; // Reset to prevent triple tap
        } else {
          this.onTap(e);
          this.lastTapTime = now;
        }
      }
    }

    // Trigger touchend event
    this.triggerEvent('touchend', {
      x: this.touchEndX,
      y: this.touchEndY,
      deltaX,
      deltaY,
      deltaTime
    });
  }

  handleTouchCancel(e) {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    this.triggerEvent('touchcancel', {});
  }

  onSwipe(deltaX, deltaY) {
    let direction;
    
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
      // Horizontal swipe
      direction = deltaX > 0 ? 'right' : 'left';
    } else {
      // Vertical swipe
      direction = deltaY > 0 ? 'down' : 'up';
    }

    this.triggerEvent('swipe', {
      direction,
      deltaX,
      deltaY
    });

    // Trigger specific swipe direction event
    this.triggerEvent(`swipe${direction}`, {
      deltaX,
      deltaY
    });
  }

  onTap(e) {
    this.triggerEvent('tap', {
      x: this.touchEndX,
      y: this.touchEndY
    });
  }

  onDoubleTap(e) {
    this.triggerEvent('doubletap', {
      x: this.touchEndX,
      y: this.touchEndY
    });
  }

  onLongPress(e) {
    this.triggerEvent('longpress', {
      x: this.touchStartX,
      y: this.touchStartY
    });
  }

  triggerEvent(eventName, detail) {
    const event = new CustomEvent(eventName, {
      detail,
      bubbles: true,
      cancelable: true
    });
    this.element.dispatchEvent(event);
  }

  destroy() {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
    }
    // Remove event listeners
    this.element.removeEventListener('touchstart', this.handleTouchStart);
    this.element.removeEventListener('touchmove', this.handleTouchMove);
    this.element.removeEventListener('touchend', this.handleTouchEnd);
    this.element.removeEventListener('touchcancel', this.handleTouchCancel);
  }
}

// Enhanced Carousel with Touch Support
class TouchCarousel {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.track = this.container.querySelector('.carousel-track');
    if (!this.track) return;

    this.options = {
      itemsPerPage: options.itemsPerPage || 5,
      gap: options.gap || 16,
      snapToItems: options.snapToItems !== false,
      ...options
    };

    this.currentIndex = 0;
    this.isDragging = false;
    this.startX = 0;
    this.currentX = 0;
    this.translateX = 0;

    this.init();
  }

  init() {
    // Enable touch gestures
    this.gestures = new TouchGestures(this.container, {
      swipeThreshold: 30
    });

    // Listen to swipe events
    this.container.addEventListener('swipeleft', () => this.next());
    this.container.addEventListener('swiperight', () => this.previous());

    // Enable smooth scrolling
    this.track.style.transition = 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
  }

  next() {
    const items = this.track.children;
    const maxIndex = items.length - this.options.itemsPerPage;
    
    if (this.currentIndex < maxIndex) {
      this.currentIndex++;
      this.updatePosition();
    }
  }

  previous() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.updatePosition();
    }
  }

  updatePosition() {
    const items = this.track.children;
    if (items.length === 0) return;

    const itemWidth = items[0].offsetWidth;
    const translateX = -(this.currentIndex * (itemWidth + this.options.gap));
    
    this.track.style.transform = `translateX(${translateX}px)`;
  }

  destroy() {
    if (this.gestures) {
      this.gestures.destroy();
    }
  }
}

// Pull to Refresh
class PullToRefresh {
  constructor(containerId, onRefresh) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.onRefresh = onRefresh;
    this.threshold = 80;
    this.startY = 0;
    this.currentY = 0;
    this.isRefreshing = false;

    this.init();
  }

  init() {
    this.container.addEventListener('touchstart', this.handleTouchStart.bind(this));
    this.container.addEventListener('touchmove', this.handleTouchMove.bind(this));
    this.container.addEventListener('touchend', this.handleTouchEnd.bind(this));
  }

  handleTouchStart(e) {
    if (this.container.scrollTop === 0) {
      this.startY = e.touches[0].clientY;
    }
  }

  handleTouchMove(e) {
    if (this.isRefreshing || this.container.scrollTop > 0) return;

    this.currentY = e.touches[0].clientY;
    const pullDistance = this.currentY - this.startY;

    if (pullDistance > 0) {
      e.preventDefault();
      // Visual feedback (could add a loading indicator here)
    }
  }

  handleTouchEnd(e) {
    if (this.isRefreshing) return;

    const pullDistance = this.currentY - this.startY;

    if (pullDistance > this.threshold) {
      this.refresh();
    }

    this.startY = 0;
    this.currentY = 0;
  }

  async refresh() {
    this.isRefreshing = true;
    
    try {
      await this.onRefresh();
    } finally {
      this.isRefreshing = false;
    }
  }
}

// Export for global use
window.TouchGestures = TouchGestures;
window.TouchCarousel = TouchCarousel;
window.PullToRefresh = PullToRefresh;
