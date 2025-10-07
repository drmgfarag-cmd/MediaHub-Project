// Hero Banner Component - MediaHub v5.5

class HeroBanner {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`Hero banner container #${containerId} not found`);
      return;
    }

    this.options = {
      autoRotate: options.autoRotate !== false,
      rotateInterval: options.rotateInterval || 7000,
      transitionDuration: options.transitionDuration || 800,
      ...options
    };

    this.currentSlide = 0;
    this.slides = [];
    this.autoRotateTimer = null;
    this.isTransitioning = false;

    this.init();
  }

  async init() {
    // Fetch featured content
    await this.loadFeaturedContent();
    
    // Render hero banner
    this.render();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Start auto-rotate
    if (this.options.autoRotate && this.slides.length > 1) {
      this.startAutoRotate();
    }
  }

  async loadFeaturedContent() {
    try {
      const response = await fetch('/api/home/hero');
      if (!response.ok) {
        // Fallback to mock data if API not available
        this.slides = this.getMockSlides();
        return;
      }
      const data = await response.json();
      this.slides = data.items || this.getMockSlides();
    } catch (error) {
      console.warn('Failed to load hero content, using mock data:', error);
      this.slides = this.getMockSlides();
    }
  }

  getMockSlides() {
    return [
      {
        id: 1,
        title: 'The Matrix Resurrections',
        year: 2021,
        rating: 8.7,
        quality: '4K',
        description: 'Return to a world of two realities: one, everyday life; the other, what lies behind it.',
        backdrop: '/api/placeholder/1920/1080?text=Matrix',
        mediaType: 'movie'
      },
      {
        id: 2,
        title: 'Stranger Things',
        year: 2022,
        rating: 9.1,
        quality: 'HD',
        description: 'When a young boy disappears, his mother, a police chief and his friends must confront terrifying supernatural forces.',
        backdrop: '/api/placeholder/1920/1080?text=Stranger+Things',
        mediaType: 'tv'
      },
      {
        id: 3,
        title: 'Dune',
        year: 2021,
        rating: 8.5,
        quality: '4K',
        description: 'A noble family becomes embroiled in a war for control over the galaxy\'s most valuable asset.',
        backdrop: '/api/placeholder/1920/1080?text=Dune',
        mediaType: 'movie'
      }
    ];
  }

  render() {
    const html = `
      <div class="hero-slides">
        ${this.slides.map((slide, index) => this.renderSlide(slide, index)).join('')}
      </div>
      <div class="hero-gradient"></div>
      ${this.renderNavigation()}
      ${this.renderArrows()}
    `;
    this.container.innerHTML = html;
  }

  renderSlide(slide, index) {
    const isActive = index === this.currentSlide ? 'active' : '';
    return `
      <div class="hero-slide ${isActive}" data-slide="${index}" style="background-image: url('${slide.backdrop}')">
        <div class="hero-content">
          <h1 class="hero-title">${slide.title}</h1>
          <div class="hero-meta">
            <span>${slide.year}</span>
            <span class="rating">
              <span class="rating-star">★</span>
              <span>${slide.rating}</span>
            </span>
            ${slide.quality ? `<span class="quality-badge">${slide.quality}</span>` : ''}
          </div>
          <p class="hero-description">${slide.description}</p>
          <div class="hero-actions">
            <button class="hero-btn hero-btn-primary" onclick="heroBanner.play(${slide.id}, '${slide.mediaType}')">
              <span>▶</span>
              <span>Play Now</span>
            </button>
            <button class="hero-btn hero-btn-secondary" onclick="heroBanner.showInfo(${slide.id})">
              <span>ℹ</span>
              <span>More Info</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  renderNavigation() {
    if (this.slides.length <= 1) return '';
    
    return `
      <div class="hero-nav">
        ${this.slides.map((_, index) => {
          const isActive = index === this.currentSlide ? 'active' : '';
          return `<div class="hero-dot ${isActive}" data-slide="${index}"></div>`;
        }).join('')}
      </div>
    `;
  }

  renderArrows() {
    if (this.slides.length <= 1) return '';
    
    return `
      <button class="hero-arrow hero-arrow-prev" aria-label="Previous slide">‹</button>
      <button class="hero-arrow hero-arrow-next" aria-label="Next slide">›</button>
    `;
  }

  setupEventListeners() {
    // Dot navigation
    this.container.querySelectorAll('.hero-dot').forEach(dot => {
      dot.addEventListener('click', (e) => {
        const slideIndex = parseInt(e.target.dataset.slide);
        this.goToSlide(slideIndex);
      });
    });

    // Arrow navigation
    const prevArrow = this.container.querySelector('.hero-arrow-prev');
    const nextArrow = this.container.querySelector('.hero-arrow-next');
    
    if (prevArrow) {
      prevArrow.addEventListener('click', () => this.previousSlide());
    }
    
    if (nextArrow) {
      nextArrow.addEventListener('click', () => this.nextSlide());
    }

    // Pause on hover
    this.container.addEventListener('mouseenter', () => this.stopAutoRotate());
    this.container.addEventListener('mouseleave', () => {
      if (this.options.autoRotate) this.startAutoRotate();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') this.previousSlide();
      if (e.key === 'ArrowRight') this.nextSlide();
    });
  }

  goToSlide(index) {
    if (this.isTransitioning || index === this.currentSlide) return;
    
    this.isTransitioning = true;
    
    // Update slides
    const slides = this.container.querySelectorAll('.hero-slide');
    slides[this.currentSlide].classList.remove('active');
    slides[index].classList.add('active');
    
    // Update dots
    const dots = this.container.querySelectorAll('.hero-dot');
    if (dots.length > 0) {
      dots[this.currentSlide].classList.remove('active');
      dots[index].classList.add('active');
    }
    
    this.currentSlide = index;
    
    setTimeout(() => {
      this.isTransitioning = false;
    }, this.options.transitionDuration);
    
    // Reset auto-rotate timer
    if (this.options.autoRotate) {
      this.stopAutoRotate();
      this.startAutoRotate();
    }
  }

  nextSlide() {
    const nextIndex = (this.currentSlide + 1) % this.slides.length;
    this.goToSlide(nextIndex);
  }

  previousSlide() {
    const prevIndex = (this.currentSlide - 1 + this.slides.length) % this.slides.length;
    this.goToSlide(prevIndex);
  }

  startAutoRotate() {
    this.stopAutoRotate();
    this.autoRotateTimer = setInterval(() => {
      this.nextSlide();
    }, this.options.rotateInterval);
  }

  stopAutoRotate() {
    if (this.autoRotateTimer) {
      clearInterval(this.autoRotateTimer);
      this.autoRotateTimer = null;
    }
  }

  play(mediaId, mediaType) {
    console.log(`Playing ${mediaType} with ID: ${mediaId}`);
    // Implement play functionality
    window.location.href = `/player.html?id=${mediaId}&type=${mediaType}`;
  }

  showInfo(mediaId) {
    console.log(`Showing info for media ID: ${mediaId}`);
    // Implement info modal
    window.location.href = `/details.html?id=${mediaId}`;
  }

  destroy() {
    this.stopAutoRotate();
    this.container.innerHTML = '';
  }
}

// Global instance
let heroBanner;

// Auto-initialize if hero-banner element exists
document.addEventListener('DOMContentLoaded', () => {
  const heroBannerElement = document.getElementById('hero-banner');
  if (heroBannerElement) {
    heroBanner = new HeroBanner('hero-banner');
  }
});
