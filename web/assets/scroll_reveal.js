// Scroll Reveal Animations - MediaHub v5.7

class ScrollReveal {
  constructor(options = {}) {
    this.options = {
      threshold: options.threshold || 0.15,
      rootMargin: options.rootMargin || '0px 0px -100px 0px',
      animationClass: options.animationClass || 'revealed',
      delay: options.delay || 0,
      duration: options.duration || 800,
      easing: options.easing || 'cubic-bezier(0.4, 0, 0.2, 1)',
      distance: options.distance || '50px',
      origin: options.origin || 'bottom',
      reset: options.reset || false,
      ...options
    };

    this.observer = null;
    this.elements = new Map();
    this.init();
  }

  init() {
    // Check for IntersectionObserver support
    if (!('IntersectionObserver' in window)) {
      this.revealAll();
      return;
    }

    this.observer = new IntersectionObserver(
      this.onIntersection.bind(this),
      {
        threshold: this.options.threshold,
        rootMargin: this.options.rootMargin
      }
    );

    this.observeElements();
  }

  observeElements() {
    const elements = document.querySelectorAll('[data-reveal]');
    elements.forEach(element => {
      // Store original styles
      const delay = element.dataset.revealDelay || this.options.delay;
      const origin = element.dataset.revealOrigin || this.options.origin;
      const distance = element.dataset.revealDistance || this.options.distance;
      const duration = element.dataset.revealDuration || this.options.duration;
      const easing = element.dataset.revealEasing || this.options.easing;

      this.elements.set(element, {
        delay,
        origin,
        distance,
        duration,
        easing,
        revealed: false
      });

      // Set initial state
      this.setInitialState(element, origin, distance, duration, easing);

      // Observe element
      this.observer.observe(element);
    });
  }

  setInitialState(element, origin, distance, duration, easing) {
    element.style.opacity = '0';
    element.style.transition = `opacity ${duration}ms ${easing}, transform ${duration}ms ${easing}`;

    switch (origin) {
      case 'top':
        element.style.transform = `translateY(-${distance})`;
        break;
      case 'bottom':
        element.style.transform = `translateY(${distance})`;
        break;
      case 'left':
        element.style.transform = `translateX(-${distance})`;
        break;
      case 'right':
        element.style.transform = `translateX(${distance})`;
        break;
      case 'scale':
        element.style.transform = 'scale(0.8)';
        break;
      default:
        element.style.transform = `translateY(${distance})`;
    }
  }

  onIntersection(entries) {
    entries.forEach(entry => {
      const element = entry.target;
      const config = this.elements.get(element);

      if (!config) return;

      if (entry.isIntersecting && !config.revealed) {
        this.reveal(element, config);
      } else if (!entry.isIntersecting && config.revealed && this.options.reset) {
        this.hide(element, config);
      }
    });
  }

  reveal(element, config) {
    setTimeout(() => {
      element.style.opacity = '1';
      element.style.transform = 'translate(0, 0) scale(1)';
      element.classList.add(this.options.animationClass);
      config.revealed = true;

      // Dispatch custom event
      element.dispatchEvent(new CustomEvent('revealed', {
        detail: { element }
      }));
    }, parseInt(config.delay));
  }

  hide(element, config) {
    const origin = config.origin;
    const distance = config.distance;

    element.style.opacity = '0';

    switch (origin) {
      case 'top':
        element.style.transform = `translateY(-${distance})`;
        break;
      case 'bottom':
        element.style.transform = `translateY(${distance})`;
        break;
      case 'left':
        element.style.transform = `translateX(-${distance})`;
        break;
      case 'right':
        element.style.transform = `translateX(${distance})`;
        break;
      case 'scale':
        element.style.transform = 'scale(0.8)';
        break;
    }

    element.classList.remove(this.options.animationClass);
    config.revealed = false;
  }

  revealAll() {
    const elements = document.querySelectorAll('[data-reveal]');
    elements.forEach(element => {
      element.style.opacity = '1';
      element.style.transform = 'translate(0, 0) scale(1)';
      element.classList.add(this.options.animationClass);
    });
  }

  refresh() {
    if (this.observer) {
      this.observer.disconnect();
      this.elements.clear();
      this.observeElements();
    }
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
    this.elements.clear();
  }
}

// Stagger Animation Helper
class StaggerReveal {
  constructor(containerSelector, options = {}) {
    this.container = document.querySelector(containerSelector);
    if (!this.container) return;

    this.options = {
      itemSelector: options.itemSelector || '.stagger-item',
      staggerDelay: options.staggerDelay || 100,
      baseDelay: options.baseDelay || 0,
      ...options
    };

    this.init();
  }

  init() {
    const items = this.container.querySelectorAll(this.options.itemSelector);
    items.forEach((item, index) => {
      const delay = this.options.baseDelay + (index * this.options.staggerDelay);
      item.setAttribute('data-reveal', '');
      item.setAttribute('data-reveal-delay', delay);
    });
  }
}

// Parallax Scroll Reveal
class ParallaxReveal {
  constructor(selector, options = {}) {
    this.elements = document.querySelectorAll(selector);
    this.options = {
      speed: options.speed || 0.5,
      ...options
    };

    this.init();
  }

  init() {
    if (this.elements.length === 0) return;

    window.addEventListener('scroll', throttle(() => {
      this.update();
    }, 16), { passive: true });

    this.update();
  }

  update() {
    const scrollTop = window.pageYOffset;

    this.elements.forEach(element => {
      const rect = element.getBoundingClientRect();
      const elementTop = rect.top + scrollTop;
      const elementHeight = rect.height;
      const windowHeight = window.innerHeight;

      // Calculate if element is in viewport
      if (scrollTop + windowHeight > elementTop && scrollTop < elementTop + elementHeight) {
        const distance = scrollTop + windowHeight - elementTop;
        const percentage = distance / (windowHeight + elementHeight);
        const movement = (percentage - 0.5) * 100 * this.options.speed;

        element.style.transform = `translateY(${movement}px)`;
      }
    });
  }
}

// Scroll Progress Indicator
class ScrollProgress {
  constructor(options = {}) {
    this.options = {
      color: options.color || '#FF6B35',
      height: options.height || '3px',
      position: options.position || 'top',
      zIndex: options.zIndex || 9999,
      ...options
    };

    this.init();
  }

  init() {
    // Create progress bar
    this.progressBar = document.createElement('div');
    this.progressBar.className = 'scroll-progress-bar';
    this.progressBar.style.cssText = `
      position: fixed;
      ${this.options.position}: 0;
      left: 0;
      width: 0;
      height: ${this.options.height};
      background: ${this.options.color};
      z-index: ${this.options.zIndex};
      transition: width 0.1s ease;
    `;

    document.body.appendChild(this.progressBar);

    // Update on scroll
    window.addEventListener('scroll', throttle(() => {
      this.update();
    }, 16), { passive: true });

    this.update();
  }

  update() {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.pageYOffset;
    const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;

    this.progressBar.style.width = `${Math.min(scrollPercent, 100)}%`;
  }

  destroy() {
    if (this.progressBar && this.progressBar.parentNode) {
      this.progressBar.parentNode.removeChild(this.progressBar);
    }
  }
}

// Export classes
window.ScrollReveal = ScrollReveal;
window.StaggerReveal = StaggerReveal;
window.ParallaxReveal = ParallaxReveal;
window.ScrollProgress = ScrollProgress;

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
  if (!window.scrollReveal) {
    window.scrollReveal = new ScrollReveal();
  }

  // Initialize scroll progress if element exists
  if (document.querySelector('[data-scroll-progress]')) {
    window.scrollProgress = new ScrollProgress();
  }
});
