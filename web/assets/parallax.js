// Parallax Scrolling Effects - MediaHub v5.7

class ParallaxScroll {
  constructor(options = {}) {
    this.options = {
      speed: options.speed || 0.5,
      direction: options.direction || 'vertical', // vertical, horizontal
      ...options
    };

    this.elements = [];
    this.ticking = false;
    this.init();
  }

  init() {
    // Find all parallax elements
    this.findParallaxElements();

    // Setup scroll listener
    window.addEventListener('scroll', this.onScroll.bind(this), { passive: true });
    window.addEventListener('resize', this.onResize.bind(this));

    // Initial update
    this.update();
  }

  findParallaxElements() {
    const elements = document.querySelectorAll('[data-parallax]');
    
    this.elements = Array.from(elements).map(el => {
      const speed = parseFloat(el.dataset.parallaxSpeed) || this.options.speed;
      const direction = el.dataset.parallaxDirection || this.options.direction;
      
      return {
        element: el,
        speed,
        direction,
        initialOffset: this.getOffset(el)
      };
    });
  }

  getOffset(element) {
    const rect = element.getBoundingClientRect();
    return {
      top: rect.top + window.pageYOffset,
      left: rect.left + window.pageXOffset
    };
  }

  onScroll() {
    if (!this.ticking) {
      window.requestAnimationFrame(() => {
        this.update();
        this.ticking = false;
      });
      this.ticking = true;
    }
  }

  onResize() {
    // Recalculate offsets
    this.elements.forEach(item => {
      item.initialOffset = this.getOffset(item.element);
    });
    this.update();
  }

  update() {
    const scrollY = window.pageYOffset;
    const scrollX = window.pageXOffset;
    const windowHeight = window.innerHeight;

    this.elements.forEach(item => {
      const { element, speed, direction, initialOffset } = item;
      const elementTop = initialOffset.top;
      const elementInView = elementTop < scrollY + windowHeight && elementTop + element.offsetHeight > scrollY;

      if (elementInView) {
        let transform;
        
        if (direction === 'vertical') {
          const translateY = (scrollY - elementTop) * speed;
          transform = `translate3d(0, ${translateY}px, 0)`;
        } else if (direction === 'horizontal') {
          const translateX = (scrollX - initialOffset.left) * speed;
          transform = `translate3d(${translateX}px, 0, 0)`;
        }

        element.style.transform = transform;
      }
    });
  }

  destroy() {
    window.removeEventListener('scroll', this.onScroll);
    window.removeEventListener('resize', this.onResize);
  }
}

// Scroll Reveal Animation
class ScrollReveal {
  constructor(options = {}) {
    this.options = {
      threshold: options.threshold || 0.15,
      rootMargin: options.rootMargin || '0px',
      animationClass: options.animationClass || 'reveal-visible',
      ...options
    };

    this.observer = null;
    this.init();
  }

  init() {
    // Create Intersection Observer
    this.observer = new IntersectionObserver(
      this.onIntersection.bind(this),
      {
        threshold: this.options.threshold,
        rootMargin: this.options.rootMargin
      }
    );

    // Observe all reveal elements
    this.observeElements();
  }

  observeElements() {
    const elements = document.querySelectorAll('[data-reveal]');
    elements.forEach(el => {
      // Add initial hidden state
      el.classList.add('reveal-hidden');
      this.observer.observe(el);
    });
  }

  onIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const element = entry.target;
        const delay = parseInt(element.dataset.revealDelay) || 0;

        setTimeout(() => {
          element.classList.remove('reveal-hidden');
          element.classList.add(this.options.animationClass);
          
          // Unobserve after reveal (one-time animation)
          if (element.dataset.revealOnce !== 'false') {
            this.observer.unobserve(element);
          }
        }, delay);
      } else {
        // Re-hide if revealOnce is false
        if (entry.target.dataset.revealOnce === 'false') {
          entry.target.classList.remove(this.options.animationClass);
          entry.target.classList.add('reveal-hidden');
        }
      }
    });
  }

  destroy() {
    if (this.observer) {
      this.observer.disconnect();
    }
  }
}

// Smooth Scroll to Element
class SmoothScroller {
  constructor(options = {}) {
    this.options = {
      duration: options.duration || 800,
      easing: options.easing || 'easeInOutCubic',
      offset: options.offset || 0,
      ...options
    };

    this.init();
  }

  init() {
    // Handle anchor links
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"]');
      if (link) {
        e.preventDefault();
        const targetId = link.getAttribute('href').substring(1);
        const target = document.getElementById(targetId);
        
        if (target) {
          this.scrollTo(target);
        }
      }
    });
  }

  scrollTo(target, customOptions = {}) {
    const options = { ...this.options, ...customOptions };
    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - options.offset;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / options.duration, 1);
      const easeProgress = this.easing(progress, options.easing);
      
      window.scrollTo(0, startPosition + distance * easeProgress);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }

  easing(t, type) {
    const easings = {
      linear: t => t,
      easeInQuad: t => t * t,
      easeOutQuad: t => t * (2 - t),
      easeInOutQuad: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
      easeInCubic: t => t * t * t,
      easeOutCubic: t => (--t) * t * t + 1,
      easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
    };

    return easings[type] ? easings[type](t) : easings.easeInOutCubic(t);
  }
}

// Add reveal animation CSS
const style = document.createElement('style');
style.textContent = `
  .reveal-hidden {
    opacity: 0;
    transform: translateY(30px);
  }

  .reveal-visible {
    opacity: 1;
    transform: translateY(0);
    transition: opacity 0.6s ease-out, transform 0.6s ease-out;
  }

  /* Parallax container */
  [data-parallax] {
    will-change: transform;
    backface-visibility: hidden;
  }
`;
document.head.appendChild(style);

// Export for global use
window.ParallaxScroll = ParallaxScroll;
window.ParallaxEffect = ParallaxScroll; // Alias for compatibility
window.ScrollReveal = ScrollReveal;
window.SmoothScroller = SmoothScroller;

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
  if (!window.parallaxScroll) {
    window.parallaxScroll = new ParallaxScroll();
  }

  if (!window.scrollReveal) {
    window.scrollReveal = new ScrollReveal();
  }

  if (!window.smoothScroller) {
    window.smoothScroller = new SmoothScroller();
  }
});
