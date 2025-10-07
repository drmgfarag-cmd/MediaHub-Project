// Page Transitions - MediaHub v5.7

class PageTransition {
  constructor(options = {}) {
    this.options = {
      duration: options.duration || 500,
      easing: options.easing || 'cubic-bezier(0.4, 0, 0.2, 1)',
      type: options.type || 'fade', // fade, slide, scale, blur
      ...options
    };

    this.isTransitioning = false;
    this.init();
  }

  init() {
    // Intercept navigation clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (link && link.href && !link.target && this.isInternalLink(link.href)) {
        e.preventDefault();
        this.navigateTo(link.href);
      }
    });

    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
      if (e.state && e.state.url) {
        this.loadPage(e.state.url, false);
      }
    });

    // Initial page load animation
    this.animatePageIn();
  }

  isInternalLink(url) {
    try {
      const linkUrl = new URL(url);
      return linkUrl.origin === window.location.origin;
    } catch {
      return false;
    }
  }

  async navigateTo(url) {
    if (this.isTransitioning) return;

    this.isTransitioning = true;

    // Animate current page out
    await this.animatePageOut();

    // Load new page
    await this.loadPage(url, true);

    // Animate new page in
    await this.animatePageIn();

    this.isTransitioning = false;
  }

  async loadPage(url, pushState = true) {
    try {
      const response = await fetch(url);
      const html = await response.text();

      // Parse HTML
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');

      // Update title
      document.title = doc.title;

      // Update content
      const newContent = doc.querySelector('main') || doc.body;
      const currentContent = document.querySelector('main') || document.body;
      currentContent.innerHTML = newContent.innerHTML;

      // Update URL
      if (pushState) {
        window.history.pushState({ url }, '', url);
      }

      // Scroll to top
      window.scrollTo(0, 0);

      // Trigger page loaded event
      window.dispatchEvent(new CustomEvent('pageloaded', { detail: { url } }));
    } catch (error) {
      console.error('Page load error:', error);
      // Fallback to normal navigation
      window.location.href = url;
    }
  }

  async animatePageOut() {
    const content = document.querySelector('main') || document.body;
    
    return new Promise((resolve) => {
      switch (this.options.type) {
        case 'fade':
          this.fadeOut(content, resolve);
          break;
        case 'slide':
          this.slideOut(content, resolve);
          break;
        case 'scale':
          this.scaleOut(content, resolve);
          break;
        case 'blur':
          this.blurOut(content, resolve);
          break;
        default:
          this.fadeOut(content, resolve);
      }
    });
  }

  async animatePageIn() {
    const content = document.querySelector('main') || document.body;
    
    return new Promise((resolve) => {
      switch (this.options.type) {
        case 'fade':
          this.fadeIn(content, resolve);
          break;
        case 'slide':
          this.slideIn(content, resolve);
          break;
        case 'scale':
          this.scaleIn(content, resolve);
          break;
        case 'blur':
          this.blurIn(content, resolve);
          break;
        default:
          this.fadeIn(content, resolve);
      }
    });
  }

  fadeOut(element, callback) {
    element.style.transition = `opacity ${this.options.duration}ms ${this.options.easing}`;
    element.style.opacity = '0';
    setTimeout(callback, this.options.duration);
  }

  fadeIn(element, callback) {
    element.style.opacity = '0';
    setTimeout(() => {
      element.style.transition = `opacity ${this.options.duration}ms ${this.options.easing}`;
      element.style.opacity = '1';
      setTimeout(callback, this.options.duration);
    }, 50);
  }

  slideOut(element, callback) {
    element.style.transition = `transform ${this.options.duration}ms ${this.options.easing}, opacity ${this.options.duration}ms ${this.options.easing}`;
    element.style.transform = 'translateX(-100px)';
    element.style.opacity = '0';
    setTimeout(callback, this.options.duration);
  }

  slideIn(element, callback) {
    element.style.transform = 'translateX(100px)';
    element.style.opacity = '0';
    setTimeout(() => {
      element.style.transition = `transform ${this.options.duration}ms ${this.options.easing}, opacity ${this.options.duration}ms ${this.options.easing}`;
      element.style.transform = 'translateX(0)';
      element.style.opacity = '1';
      setTimeout(callback, this.options.duration);
    }, 50);
  }

  scaleOut(element, callback) {
    element.style.transition = `transform ${this.options.duration}ms ${this.options.easing}, opacity ${this.options.duration}ms ${this.options.easing}`;
    element.style.transform = 'scale(0.9)';
    element.style.opacity = '0';
    setTimeout(callback, this.options.duration);
  }

  scaleIn(element, callback) {
    element.style.transform = 'scale(1.1)';
    element.style.opacity = '0';
    setTimeout(() => {
      element.style.transition = `transform ${this.options.duration}ms ${this.options.easing}, opacity ${this.options.duration}ms ${this.options.easing}`;
      element.style.transform = 'scale(1)';
      element.style.opacity = '1';
      setTimeout(callback, this.options.duration);
    }, 50);
  }

  blurOut(element, callback) {
    element.style.transition = `filter ${this.options.duration}ms ${this.options.easing}, opacity ${this.options.duration}ms ${this.options.easing}`;
    element.style.filter = 'blur(10px)';
    element.style.opacity = '0';
    setTimeout(callback, this.options.duration);
  }

  blurIn(element, callback) {
    element.style.filter = 'blur(10px)';
    element.style.opacity = '0';
    setTimeout(() => {
      element.style.transition = `filter ${this.options.duration}ms ${this.options.easing}, opacity ${this.options.duration}ms ${this.options.easing}`;
      element.style.filter = 'blur(0)';
      element.style.opacity = '1';
      setTimeout(callback, this.options.duration);
    }, 50);
  }
}

// Micro-interactions
class MicroInteractions {
  constructor() {
    this.init();
  }

  init() {
    this.setupButtonFeedback();
    this.setupCardInteractions();
    this.setupInputFeedback();
    this.setupTooltips();
  }

  setupButtonFeedback() {
    document.addEventListener('click', (e) => {
      const button = e.target.closest('button, .btn, [role="button"]');
      if (button && !button.disabled) {
        this.createRipple(button, e);
        this.buttonPressAnimation(button);
      }
    });
  }

  createRipple(element, event) {
    const ripple = document.createElement('span');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.cssText = `
      position: absolute;
      width: ${size}px;
      height: ${size}px;
      left: ${x}px;
      top: ${y}px;
      background: rgba(255, 255, 255, 0.5);
      border-radius: 50%;
      transform: scale(0);
      animation: ripple-animation 0.6s ease-out;
      pointer-events: none;
    `;

    // Ensure element has position relative
    if (getComputedStyle(element).position === 'static') {
      element.style.position = 'relative';
    }
    element.style.overflow = 'hidden';

    element.appendChild(ripple);

    setTimeout(() => ripple.remove(), 600);
  }

  buttonPressAnimation(button) {
    button.style.transform = 'scale(0.95)';
    setTimeout(() => {
      button.style.transform = '';
    }, 100);
  }

  setupCardInteractions() {
    document.addEventListener('mouseenter', (e) => {
      const card = e.target.closest('.card, .media-card, .carousel-item');
      if (card) {
        this.cardHoverIn(card);
      }
    }, true);

    document.addEventListener('mouseleave', (e) => {
      const card = e.target.closest('.card, .media-card, .carousel-item');
      if (card) {
        this.cardHoverOut(card);
      }
    }, true);
  }

  cardHoverIn(card) {
    card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
    card.style.transform = 'translateY(-8px) scale(1.02)';
    card.style.boxShadow = '0 16px 32px rgba(0, 0, 0, 0.4)';
  }

  cardHoverOut(card) {
    card.style.transform = '';
    card.style.boxShadow = '';
  }

  setupInputFeedback() {
    document.addEventListener('focus', (e) => {
      const input = e.target.closest('input, textarea, select');
      if (input) {
        this.inputFocusIn(input);
      }
    }, true);

    document.addEventListener('blur', (e) => {
      const input = e.target.closest('input, textarea, select');
      if (input) {
        this.inputFocusOut(input);
      }
    }, true);
  }

  inputFocusIn(input) {
    input.style.transition = 'border-color 0.3s ease, box-shadow 0.3s ease';
    input.style.borderColor = '#FF6B35';
    input.style.boxShadow = '0 0 0 3px rgba(255, 107, 53, 0.1)';
  }

  inputFocusOut(input) {
    input.style.borderColor = '';
    input.style.boxShadow = '';
  }

  setupTooltips() {
    document.addEventListener('mouseenter', (e) => {
      const element = e.target.closest('[data-tooltip]');
      if (element) {
        this.showTooltip(element);
      }
    }, true);

    document.addEventListener('mouseleave', (e) => {
      const element = e.target.closest('[data-tooltip]');
      if (element) {
        this.hideTooltip(element);
      }
    }, true);
  }

  showTooltip(element) {
    const text = element.dataset.tooltip;
    if (!text) return;

    const tooltip = document.createElement('div');
    tooltip.className = 'micro-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
      position: absolute;
      background: rgba(0, 0, 0, 0.9);
      color: white;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 13px;
      white-space: nowrap;
      z-index: 10000;
      pointer-events: none;
      animation: fadeInUp 0.2s ease-out;
    `;

    document.body.appendChild(tooltip);

    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    
    tooltip.style.left = `${rect.left + rect.width / 2 - tooltipRect.width / 2}px`;
    tooltip.style.top = `${rect.top - tooltipRect.height - 8}px`;

    element._tooltip = tooltip;
  }

  hideTooltip(element) {
    if (element._tooltip) {
      element._tooltip.remove();
      delete element._tooltip;
    }
  }
}

// Add ripple animation CSS
const style = document.createElement('style');
style.textContent = `
  @keyframes ripple-animation {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Export for global use
window.PageTransition = PageTransition;
window.MicroInteractions = MicroInteractions;

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
  // Initialize page transitions
  if (!window.pageTransitions) {
    window.pageTransitions = new PageTransition({
      type: 'fade',
      duration: 400
    });
  }

  // Initialize micro-interactions
  if (!window.microInteractions) {
    window.microInteractions = new MicroInteractions();
  }
});
