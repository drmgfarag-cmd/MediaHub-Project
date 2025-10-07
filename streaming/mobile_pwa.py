#!/usr/bin/env python3
"""
Mobile Progressive Web App Interface
Phase 1A Streaming Infrastructure Component

Provides PWA manifest and service worker, mobile-responsive design,
offline capabilities, push notifications, and app-like experience on mobile devices.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from flask import Flask, Response, request, jsonify, send_from_directory, render_template_string


class MobilePWAManager:
    """Manages Progressive Web App features for mobile interface"""
    
    def __init__(self, app_name: str = "MediaHub", app_root: str = "static/pwa"):
        self.app_name = app_name
        self.app_root = Path(app_root)
        self.app_root.mkdir(parents=True, exist_ok=True)
        self.setup_pwa_files()
    
    def setup_pwa_files(self):
        """Create PWA manifest and service worker files"""
        self._create_manifest()
        self._create_service_worker()
        self._create_mobile_interface()
        self._create_offline_page()
        self._create_icons()
    
    def _create_manifest(self):
        """Create PWA manifest.json file"""
        manifest = {
            "name": f"{self.app_name} - Media Streaming",
            "short_name": self.app_name,
            "description": "Stream and manage your media content on any device",
            "start_url": "/mobile",
            "display": "standalone",
            "background_color": "#0f0f0f",
            "theme_color": "#569cd6",
            "orientation": "any",
            "scope": "/",
            "lang": "en",
            "dir": "ltr",
            "categories": ["entertainment", "multimedia", "utilities"],
            "prefer_related_applications": False,
            "icons": [
                {
                    "src": "/static/pwa/icons/icon-72x72.png",
                    "sizes": "72x72",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/pwa/icons/icon-96x96.png",
                    "sizes": "96x96",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/pwa/icons/icon-128x128.png",
                    "sizes": "128x128",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/pwa/icons/icon-144x144.png",
                    "sizes": "144x144",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/pwa/icons/icon-152x152.png",
                    "sizes": "152x152",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/pwa/icons/icon-192x192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/pwa/icons/icon-384x384.png",
                    "sizes": "384x384",
                    "type": "image/png",
                    "purpose": "any"
                },
                {
                    "src": "/static/pwa/icons/icon-512x512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable"
                }
            ],
            "screenshots": [
                {
                    "src": "/static/pwa/screenshots/mobile-1.png",
                    "sizes": "640x1136",
                    "type": "image/png",
                    "form_factor": "narrow"
                },
                {
                    "src": "/static/pwa/screenshots/desktop-1.png",
                    "sizes": "1280x720",
                    "type": "image/png",
                    "form_factor": "wide"
                }
            ],
            "related_applications": [],
            "protocol_handlers": [
                {
                    "protocol": "web+mediahub",
                    "url": "/mobile/handle?url=%s"
                }
            ],
            "file_handlers": [
                {
                    "action": "/mobile/handle-file",
                    "accept": {
                        "video/*": [".mp4", ".mkv", ".avi", ".mov"],
                        "audio/*": [".mp3", ".flac", ".wav", ".aac"]
                    }
                }
            ],
            "share_target": {
                "action": "/mobile/share",
                "method": "POST",
                "enctype": "multipart/form-data",
                "params": {
                    "title": "title",
                    "text": "text",
                    "url": "url",
                    "files": [
                        {
                            "name": "media",
                            "accept": ["video/*", "audio/*"]
                        }
                    ]
                }
            }
        }
        
        manifest_path = self.app_root / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def _create_service_worker(self):
        """Create service worker for offline functionality"""
        service_worker = '''
const CACHE_NAME = 'mediahub-v1';
const OFFLINE_URL = '/offline';

// Files to cache for offline use
const CACHE_FILES = [
  '/',
  '/mobile',
  '/offline',
  '/static/pwa/mobile.css',
  '/static/pwa/mobile.js',
  '/static/pwa/icons/icon-192x192.png',
  '/static/pwa/icons/icon-512x512.png'
];

// Install event - cache essential files
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching app files...');
        return cache.addAll(CACHE_FILES);
      })
      .then(() => {
        console.log('Service Worker installed successfully');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Handle navigation requests
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.open(CACHE_NAME)
            .then((cache) => {
              return cache.match(OFFLINE_URL);
            });
        })
    );
    return;
  }
  
  // Handle other requests with cache-first strategy
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version if available
        if (response) {
          return response;
        }
        
        // Otherwise fetch from network
        return fetch(event.request)
          .then((response) => {
            // Cache successful responses
            if (response.status === 200) {
              const responseClone = response.clone();
              caches.open(CACHE_NAME)
                .then((cache) => {
                  cache.put(event.request, responseClone);
                });
            }
            return response;
          })
          .catch(() => {
            // Return offline page for failed requests
            if (event.request.destination === 'document') {
              return caches.match(OFFLINE_URL);
            }
          });
      })
  );
});

// Background sync for when connection is restored
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Sync pending actions when online
      syncPendingActions()
    );
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New content available',
    icon: '/static/pwa/icons/icon-192x192.png',
    badge: '/static/pwa/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Open App',
        icon: '/static/pwa/icons/icon-192x192.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/pwa/icons/icon-192x192.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('MediaHub', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/mobile')
    );
  }
});

// Helper function to sync pending actions
function syncPendingActions() {
  return new Promise((resolve) => {
    // Implement sync logic here
    console.log('Syncing pending actions...');
    resolve();
  });
}
'''
        
        sw_path = self.app_root / "sw.js"
        with open(sw_path, 'w') as f:
            f.write(service_worker)
    
    def _create_mobile_interface(self):
        """Create mobile-optimized HTML interface"""
        mobile_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#569cd6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="MediaHub">
    
    <title>MediaHub - Mobile</title>
    
    <!-- PWA Manifest -->
    <link rel="manifest" href="/static/pwa/manifest.json">
    
    <!-- Icons -->
    <link rel="icon" type="image/png" sizes="32x32" href="/static/pwa/icons/icon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/static/pwa/icons/icon-16x16.png">
    <link rel="apple-touch-icon" href="/static/pwa/icons/icon-180x180.png">
    
    <!-- Styles -->
    <link rel="stylesheet" href="/static/pwa/mobile.css">
</head>
<body>
    <div id="app">
        <!-- Header -->
        <header class="app-header">
            <div class="header-content">
                <h1 class="app-title">MediaHub</h1>
                <button class="menu-toggle" id="menuToggle">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>
        </header>
        
        <!-- Navigation -->
        <nav class="app-nav" id="appNav">
            <a href="#home" class="nav-item active" data-page="home">
                <i class="icon-home"></i>
                <span>Home</span>
            </a>
            <a href="#library" class="nav-item" data-page="library">
                <i class="icon-library"></i>
                <span>Library</span>
            </a>
            <a href="#streaming" class="nav-item" data-page="streaming">
                <i class="icon-cast"></i>
                <span>Cast</span>
            </a>
            <a href="#downloads" class="nav-item" data-page="downloads">
                <i class="icon-download"></i>
                <span>Downloads</span>
            </a>
            <a href="#settings" class="nav-item" data-page="settings">
                <i class="icon-settings"></i>
                <span>Settings</span>
            </a>
        </nav>
        
        <!-- Main Content -->
        <main class="app-main">
            <!-- Home Page -->
            <section class="page active" id="homePage">
                <div class="hero-section">
                    <h2>Welcome to MediaHub</h2>
                    <p>Stream, manage, and enjoy your media content anywhere</p>
                </div>
                
                <div class="quick-actions">
                    <button class="action-btn" id="quickCast">
                        <i class="icon-cast"></i>
                        <span>Quick Cast</span>
                    </button>
                    <button class="action-btn" id="addMedia">
                        <i class="icon-plus"></i>
                        <span>Add Media</span>
                    </button>
                    <button class="action-btn" id="browseLibrary">
                        <i class="icon-folder"></i>
                        <span>Browse</span>
                    </button>
                </div>
                
                <div class="recent-content">
                    <h3>Continue Watching</h3>
                    <div class="content-grid" id="recentContent">
                        <!-- Recent content will be loaded here -->
                    </div>
                </div>
            </section>
            
            <!-- Library Page -->
            <section class="page" id="libraryPage">
                <div class="page-header">
                    <h2>Media Library</h2>
                    <button class="search-btn" id="searchToggle">
                        <i class="icon-search"></i>
                    </button>
                </div>
                
                <div class="search-bar" id="searchBar">
                    <input type="text" placeholder="Search your library..." id="searchInput">
                </div>
                
                <div class="library-filters">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="videos">Videos</button>
                    <button class="filter-btn" data-filter="music">Music</button>
                    <button class="filter-btn" data-filter="photos">Photos</button>
                </div>
                
                <div class="library-content" id="libraryContent">
                    <!-- Library content will be loaded here -->
                </div>
            </section>
            
            <!-- Streaming Page -->
            <section class="page" id="streamingPage">
                <div class="page-header">
                    <h2>Cast & Stream</h2>
                    <button class="refresh-btn" id="refreshDevices">
                        <i class="icon-refresh"></i>
                    </button>
                </div>
                
                <div class="devices-section">
                    <h3>Available Devices</h3>
                    <div class="devices-list" id="devicesList">
                        <!-- Discovered devices will appear here -->
                    </div>
                </div>
                
                <div class="streaming-controls" id="streamingControls" style="display: none;">
                    <h3>Now Playing</h3>
                    <div class="media-info" id="mediaInfo">
                        <!-- Current media info -->
                    </div>
                    <div class="playback-controls">
                        <button class="control-btn" id="prevBtn"><i class="icon-prev"></i></button>
                        <button class="control-btn play-pause" id="playPauseBtn"><i class="icon-play"></i></button>
                        <button class="control-btn" id="nextBtn"><i class="icon-next"></i></button>
                    </div>
                    <div class="volume-control">
                        <i class="icon-volume"></i>
                        <input type="range" id="volumeSlider" min="0" max="100" value="50">
                    </div>
                </div>
            </section>
            
            <!-- Downloads Page -->
            <section class="page" id="downloadsPage">
                <div class="page-header">
                    <h2>Downloads</h2>
                    <button class="add-btn" id="addDownload">
                        <i class="icon-plus"></i>
                    </button>
                </div>
                
                <div class="downloads-list" id="downloadsList">
                    <!-- Download items will appear here -->
                </div>
            </section>
            
            <!-- Settings Page -->
            <section class="page" id="settingsPage">
                <div class="page-header">
                    <h2>Settings</h2>
                </div>
                
                <div class="settings-groups">
                    <div class="settings-group">
                        <h3>Streaming</h3>
                        <div class="setting-item">
                            <label>Auto-discover devices</label>
                            <input type="checkbox" id="autoDiscover" checked>
                        </div>
                        <div class="setting-item">
                            <label>Streaming quality</label>
                            <select id="streamingQuality">
                                <option value="auto">Auto</option>
                                <option value="1080p">1080p</option>
                                <option value="720p">720p</option>
                                <option value="480p">480p</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="settings-group">
                        <h3>Notifications</h3>
                        <div class="setting-item">
                            <label>Push notifications</label>
                            <input type="checkbox" id="pushNotifications">
                        </div>
                        <div class="setting-item">
                            <label>Download complete</label>
                            <input type="checkbox" id="downloadNotifications" checked>
                        </div>
                    </div>
                    
                    <div class="settings-group">
                        <h3>Storage</h3>
                        <div class="setting-item">
                            <label>Offline storage</label>
                            <button class="btn-secondary" id="manageStorage">Manage</button>
                        </div>
                        <div class="setting-item">
                            <label>Clear cache</label>
                            <button class="btn-secondary" id="clearCache">Clear</button>
                        </div>
                    </div>
                </div>
            </section>
        </main>
        
        <!-- Install Prompt -->
        <div class="install-prompt" id="installPrompt" style="display: none;">
            <div class="prompt-content">
                <h3>Install MediaHub</h3>
                <p>Get the full app experience with offline access and notifications.</p>
                <div class="prompt-actions">
                    <button class="btn-secondary" id="dismissInstall">Not now</button>
                    <button class="btn-primary" id="installApp">Install</button>
                </div>
            </div>
        </div>
        
        <!-- Loading Overlay -->
        <div class="loading-overlay" id="loadingOverlay" style="display: none;">
            <div class="loading-spinner"></div>
            <p>Loading...</p>
        </div>
    </div>
    
    <!-- Scripts -->
    <script src="/static/pwa/mobile.js"></script>
</body>
</html>
'''
        
        mobile_path = self.app_root / "mobile.html"
        with open(mobile_path, 'w') as f:
            f.write(mobile_html)
    
    def _create_offline_page(self):
        """Create offline fallback page"""
        offline_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#569cd6">
    <title>MediaHub - Offline</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f0f;
            color: #ffffff;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            text-align: center;
        }
        .offline-container {
            max-width: 400px;
            padding: 2rem;
        }
        .offline-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.7;
        }
        h1 {
            color: #569cd6;
            margin-bottom: 1rem;
        }
        p {
            color: #cccccc;
            line-height: 1.6;
            margin-bottom: 2rem;
        }
        .retry-btn {
            background: #569cd6;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 1rem;
            transition: background 0.3s;
        }
        .retry-btn:hover {
            background: #4a8bc2;
        }
    </style>
</head>
<body>
    <div class="offline-container">
        <div class="offline-icon">📶</div>
        <h1>You're Offline</h1>
        <p>It looks like you've lost your internet connection. Some features may not be available until you're back online.</p>
        <button class="retry-btn" onclick="window.location.reload()">Try Again</button>
    </div>
</body>
</html>
'''
        
        offline_path = self.app_root / "offline.html"
        with open(offline_path, 'w') as f:
            f.write(offline_html)
    
    def _create_icons(self):
        """Create placeholder icon files (in a real implementation, these would be actual PNG files)"""
        icons_dir = self.app_root / "icons"
        icons_dir.mkdir(exist_ok=True)
        
        # Create simple SVG icons that can be converted to PNG
        icon_sizes = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512]
        
        svg_template = '''
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{size}" height="{size}" fill="#569cd6"/>
  <text x="50%" y="50%" text-anchor="middle" dy="0.3em" fill="white" font-family="Arial, sans-serif" font-size="{text_size}">MH</text>
</svg>
'''
        
        for size in icon_sizes:
            text_size = size // 3
            svg_content = svg_template.format(size=size, text_size=text_size)
            
            # For demonstration, save as SVG (in production, convert to PNG)
            icon_path = icons_dir / f"icon-{size}x{size}.svg"
            with open(icon_path, 'w') as f:
                f.write(svg_content)
    
    def setup_flask_routes(self, app: Flask):
        """Setup Flask routes for PWA functionality"""
        
        @app.route('/manifest.json')
        def serve_manifest():
            """Serve PWA manifest"""
            return send_from_directory(self.app_root, 'manifest.json')
        
        @app.route('/sw.js')
        def serve_service_worker():
            """Serve service worker"""
            response = send_from_directory(self.app_root, 'sw.js')
            response.headers['Cache-Control'] = 'no-cache'
            return response
        
        @app.route('/mobile')
        def mobile_interface():
            """Serve mobile PWA interface"""
            return send_from_directory(self.app_root, 'mobile.html')
        
        @app.route('/offline')
        def offline_page():
            """Serve offline fallback page"""
            return send_from_directory(self.app_root, 'offline.html')
        
        @app.route('/static/pwa/<path:filename>')
        def serve_pwa_static(filename):
            """Serve PWA static files"""
            return send_from_directory(self.app_root, filename)
        
        @app.route('/api/pwa/install', methods=['POST'])
        def track_install():
            """Track PWA installation"""
            try:
                data = request.get_json() or {}
                user_agent = request.headers.get('User-Agent', '')
                
                # Log installation event
                print(f"PWA installed: {user_agent}")
                
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/pwa/push/subscribe', methods=['POST'])
        def subscribe_push():
            """Subscribe to push notifications"""
            try:
                subscription_data = request.get_json()
                
                # Store subscription data (implement your storage logic)
                print(f"Push subscription: {subscription_data}")
                
                return jsonify({'success': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/api/pwa/push/send', methods=['POST'])
        def send_push_notification():
            """Send push notification"""
            try:
                data = request.get_json()
                message = data.get('message', 'New notification from MediaHub')
                
                # Implement push notification sending logic here
                # This would typically use a service like FCM or web-push
                
                return jsonify({
                    'success': True,
                    'message': 'Notification sent'
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @app.route('/mobile/handle')
        def handle_protocol():
            """Handle custom protocol URLs"""
            url = request.args.get('url', '')
            
            # Process the custom protocol URL
            # Redirect to appropriate mobile page
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Handling Link...</title>
                <meta http-equiv="refresh" content="0; url=/mobile#handle?url={url}">
            </head>
            <body>
                <p>Handling link... <a href="/mobile#handle?url={url}">Click here if not redirected</a></p>
            </body>
            </html>
            '''
        
        @app.route('/mobile/share', methods=['POST'])
        def handle_share():
            """Handle shared content from other apps"""
            try:
                # Get shared data
                title = request.form.get('title', '')
                text = request.form.get('text', '')
                url = request.form.get('url', '')
                
                # Handle shared files
                files = request.files.getlist('media')
                
                # Process shared content
                shared_content = {
                    'title': title,
                    'text': text,
                    'url': url,
                    'files': [f.filename for f in files if f.filename]
                }
                
                # Redirect to mobile interface with shared content
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Content Shared</title>
                    <meta http-equiv="refresh" content="0; url=/mobile#shared={shared_content}">
                </head>
                <body>
                    <p>Processing shared content... <a href="/mobile">Open MediaHub</a></p>
                </body>
                </html>
                '''
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def create_mobile_css(self):
        """Create mobile-specific CSS styles"""
        css_content = '''
/* Mobile PWA Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f0f0f;
    color: #ffffff;
    overflow-x: hidden;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* App Layout */
#app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
    min-height: 100dvh;
}

/* Header */
.app-header {
    background: #1a1a1a;
    border-bottom: 1px solid #333;
    position: sticky;
    top: 0;
    z-index: 100;
    padding: env(safe-area-inset-top) 0 0 0;
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
}

.app-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: #569cd6;
}

.menu-toggle {
    background: none;
    border: none;
    display: flex;
    flex-direction: column;
    width: 24px;
    height: 18px;
    cursor: pointer;
}

.menu-toggle span {
    background: #ffffff;
    height: 2px;
    margin: 2px 0;
    transition: 0.3s;
}

/* Navigation */
.app-nav {
    background: #1a1a1a;
    border-top: 1px solid #333;
    display: flex;
    justify-content: space-around;
    padding: 0.5rem 0;
    padding-bottom: calc(0.5rem + env(safe-area-inset-bottom));
    position: sticky;
    bottom: 0;
    z-index: 100;
}

.nav-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-decoration: none;
    color: #888;
    font-size: 0.75rem;
    padding: 0.5rem;
    transition: color 0.3s;
}

.nav-item.active {
    color: #569cd6;
}

.nav-item i {
    font-size: 1.25rem;
    margin-bottom: 0.25rem;
}

/* Main Content */
.app-main {
    flex: 1;
    overflow-y: auto;
    padding-bottom: 2rem;
}

.page {
    display: none;
    padding: 1rem;
}

.page.active {
    display: block;
}

/* Page Headers */
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.page-header h2 {
    font-size: 1.5rem;
    color: #ffffff;
}

/* Hero Section */
.hero-section {
    text-align: center;
    padding: 2rem 0;
    margin-bottom: 2rem;
}

.hero-section h2 {
    font-size: 1.75rem;
    margin-bottom: 0.5rem;
    color: #569cd6;
}

.hero-section p {
    color: #cccccc;
    font-size: 1rem;
}

/* Quick Actions */
.quick-actions {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.action-btn {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 0.75rem;
    padding: 1rem;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    transition: all 0.3s;
}

.action-btn:hover {
    background: #333;
    border-color: #569cd6;
}

.action-btn i {
    font-size: 1.5rem;
    color: #569cd6;
}

/* Content Grids */
.content-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 1rem;
}

.content-item {
    background: #2a2a2a;
    border-radius: 0.5rem;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.3s;
}

.content-item:hover {
    transform: translateY(-2px);
}

.content-item img {
    width: 100%;
    height: 120px;
    object-fit: cover;
}

.content-item .info {
    padding: 0.75rem;
}

.content-item .title {
    font-size: 0.875rem;
    font-weight: 500;
    margin-bottom: 0.25rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.content-item .subtitle {
    font-size: 0.75rem;
    color: #888;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Filters */
.library-filters {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    overflow-x: auto;
    padding-bottom: 0.5rem;
}

.filter-btn {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 1rem;
    padding: 0.5rem 1rem;
    color: #ffffff;
    font-size: 0.875rem;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.3s;
}

.filter-btn.active {
    background: #569cd6;
    border-color: #569cd6;
}

/* Search */
.search-bar {
    margin-bottom: 1rem;
    display: none;
}

.search-bar.active {
    display: block;
}

.search-bar input {
    width: 100%;
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 0.5rem;
    padding: 0.75rem;
    color: #ffffff;
    font-size: 1rem;
}

.search-bar input::placeholder {
    color: #888;
}

/* Buttons */
.btn-primary {
    background: #569cd6;
    color: white;
    border: none;
    border-radius: 0.5rem;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.3s;
}

.btn-primary:hover {
    background: #4a8bc2;
}

.btn-secondary {
    background: #2a2a2a;
    color: white;
    border: 1px solid #444;
    border-radius: 0.5rem;
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.3s;
}

.btn-secondary:hover {
    background: #333;
    border-color: #569cd6;
}

/* Device List */
.devices-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
}

.device-item {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 0.5rem;
    padding: 1rem;
    cursor: pointer;
    transition: all 0.3s;
}

.device-item:hover {
    border-color: #569cd6;
}

.device-item.connected {
    border-color: #00ff00;
    background: #1a2a1a;
}

/* Controls */
.playback-controls {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin: 1rem 0;
}

.control-btn {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    cursor: pointer;
    transition: all 0.3s;
}

.control-btn:hover {
    background: #333;
    border-color: #569cd6;
}

.control-btn.play-pause {
    width: 56px;
    height: 56px;
    background: #569cd6;
    border-color: #569cd6;
}

/* Volume Control */
.volume-control {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1rem 0;
}

.volume-control input[type="range"] {
    flex: 1;
    background: #444;
    height: 4px;
    border-radius: 2px;
    outline: none;
    -webkit-appearance: none;
}

.volume-control input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #569cd6;
    cursor: pointer;
}

/* Settings */
.settings-groups {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.settings-group {
    background: #1a1a1a;
    border-radius: 0.75rem;
    padding: 1rem;
}

.settings-group h3 {
    color: #569cd6;
    margin-bottom: 1rem;
    font-size: 1.125rem;
}

.setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 0;
    border-bottom: 1px solid #333;
}

.setting-item:last-child {
    border-bottom: none;
}

.setting-item label {
    font-size: 0.875rem;
    color: #cccccc;
}

.setting-item input[type="checkbox"] {
    width: 20px;
    height: 20px;
    accent-color: #569cd6;
}

.setting-item select {
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 0.25rem;
    padding: 0.5rem;
    color: #ffffff;
    font-size: 0.875rem;
}

/* Install Prompt */
.install-prompt {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #1a1a1a;
    border-top: 1px solid #333;
    padding: 1rem;
    z-index: 200;
}

.prompt-content h3 {
    color: #569cd6;
    margin-bottom: 0.5rem;
}

.prompt-content p {
    color: #cccccc;
    font-size: 0.875rem;
    margin-bottom: 1rem;
}

.prompt-actions {
    display: flex;
    gap: 0.75rem;
}

.prompt-actions button {
    flex: 1;
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 300;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #333;
    border-top: 4px solid #569cd6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Icon Fonts (simple implementations) */
.icon-home::before { content: "🏠"; }
.icon-library::before { content: "📚"; }
.icon-cast::before { content: "📺"; }
.icon-download::before { content: "⬇️"; }
.icon-settings::before { content: "⚙️"; }
.icon-plus::before { content: "+"; }
.icon-folder::before { content: "📁"; }
.icon-search::before { content: "🔍"; }
.icon-refresh::before { content: "🔄"; }
.icon-play::before { content: "▶️"; }
.icon-pause::before { content: "⏸️"; }
.icon-prev::before { content: "⏮️"; }
.icon-next::before { content: "⏭️"; }
.icon-volume::before { content: "🔊"; }

/* Responsive Design */
@media (max-width: 480px) {
    .content-grid {
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    }
    
    .quick-actions {
        grid-template-columns: repeat(3, 1fr);
    }
    
    .prompt-actions {
        flex-direction: column;
    }
}

@media (orientation: landscape) and (max-height: 500px) {
    .hero-section {
        padding: 1rem 0;
    }
    
    .quick-actions {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* Dark theme support */
@media (prefers-color-scheme: dark) {
    /* Already using dark theme as default */
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}
'''
        
        css_path = self.app_root / "mobile.css"
        with open(css_path, 'w') as f:
            f.write(css_content)
    
    def create_mobile_js(self):
        """Create mobile-specific JavaScript functionality"""
        js_content = '''
// Mobile PWA JavaScript
class MediaHubMobile {
    constructor() {
        this.currentPage = 'home';
        this.deferredPrompt = null;
        this.isOnline = navigator.onLine;
        
        this.init();
    }
    
    init() {
        this.setupServiceWorker();
        this.setupNavigation();
        this.setupInstallPrompt();
        this.setupNetworkHandling();
        this.setupPushNotifications();
        this.bindEvents();
        
        console.log('MediaHub Mobile initialized');
    }
    
    async setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered:', registration);
                
                registration.addEventListener('updatefound', () => {
                    console.log('Service Worker update found');
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const pages = document.querySelectorAll('.page');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetPage = item.dataset.page;
                this.showPage(targetPage);
            });
        });
        
        // Handle back button
        window.addEventListener('popstate', (e) => {
            const page = e.state?.page || 'home';
            this.showPage(page, false);
        });
    }
    
    showPage(pageName, updateHistory = true) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        
        // Show target page
        const targetPage = document.getElementById(`${pageName}Page`);
        if (targetPage) {
            targetPage.classList.add('active');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[data-page="${pageName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Update history
        if (updateHistory) {
            history.pushState({ page: pageName }, '', `#${pageName}`);
        }
        
        this.currentPage = pageName;
        
        // Load page-specific content
        this.loadPageContent(pageName);
    }
    
    loadPageContent(pageName) {
        switch (pageName) {
            case 'home':
                this.loadRecentContent();
                break;
            case 'library':
                this.loadLibraryContent();
                break;
            case 'streaming':
                this.loadStreamingDevices();
                break;
            case 'downloads':
                this.loadDownloads();
                break;
        }
    }
    
    async loadRecentContent() {
        const container = document.getElementById('recentContent');
        container.innerHTML = '<div class="loading">Loading recent content...</div>';
        
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Mock recent content
            const recentItems = [
                { title: 'Movie Title', subtitle: '45 min remaining', image: '/static/pwa/placeholder.jpg' },
                { title: 'TV Show S1E5', subtitle: 'Next episode', image: '/static/pwa/placeholder.jpg' },
                { title: 'Music Album', subtitle: 'Continue listening', image: '/static/pwa/placeholder.jpg' }
            ];
            
            container.innerHTML = recentItems.map(item => `
                <div class="content-item">
                    <img src="${item.image}" alt="${item.title}" onerror="this.style.display='none'">
                    <div class="info">
                        <div class="title">${item.title}</div>
                        <div class="subtitle">${item.subtitle}</div>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            container.innerHTML = '<div class="error">Failed to load recent content</div>';
        }
    }
    
    async loadLibraryContent() {
        const container = document.getElementById('libraryContent');
        container.innerHTML = '<div class="loading">Loading library...</div>';
        
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Mock library content
            const libraryItems = Array.from({ length: 12 }, (_, i) => ({
                title: `Media Item ${i + 1}`,
                subtitle: 'Type • Duration',
                image: '/static/pwa/placeholder.jpg'
            }));
            
            container.innerHTML = `
                <div class="content-grid">
                    ${libraryItems.map(item => `
                        <div class="content-item">
                            <img src="${item.image}" alt="${item.title}" onerror="this.style.display='none'">
                            <div class="info">
                                <div class="title">${item.title}</div>
                                <div class="subtitle">${item.subtitle}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            
        } catch (error) {
            container.innerHTML = '<div class="error">Failed to load library</div>';
        }
    }
    
    async loadStreamingDevices() {
        const container = document.getElementById('devicesList');
        container.innerHTML = '<div class="loading">Discovering devices...</div>';
        
        try {
            // Simulate device discovery
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Mock discovered devices
            const devices = [
                { name: 'Living Room TV', type: 'WebOS TV', status: 'available' },
                { name: 'Bedroom Chromecast', type: 'Chromecast', status: 'available' },
                { name: 'Kitchen Speaker', type: 'DLNA Speaker', status: 'busy' }
            ];
            
            container.innerHTML = devices.map(device => `
                <div class="device-item ${device.status === 'available' ? '' : 'disabled'}" data-device="${device.name}">
                    <div class="device-info">
                        <div class="device-name">${device.name}</div>
                        <div class="device-type">${device.type}</div>
                    </div>
                    <div class="device-status">${device.status}</div>
                </div>
            `).join('');
            
            // Add click handlers for device items
            container.querySelectorAll('.device-item').forEach(item => {
                item.addEventListener('click', () => {
                    if (!item.classList.contains('disabled')) {
                        this.connectToDevice(item.dataset.device);
                    }
                });
            });
            
        } catch (error) {
            container.innerHTML = '<div class="error">Failed to discover devices</div>';
        }
    }
    
    connectToDevice(deviceName) {
        console.log('Connecting to device:', deviceName);
        
        // Show streaming controls
        const controls = document.getElementById('streamingControls');
        controls.style.display = 'block';
        
        // Update device status
        const deviceItem = document.querySelector(`[data-device="${deviceName}"]`);
        if (deviceItem) {
            deviceItem.classList.add('connected');
        }
    }
    
    async loadDownloads() {
        const container = document.getElementById('downloadsList');
        container.innerHTML = '<div class="loading">Loading downloads...</div>';
        
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Mock downloads
            const downloads = [
                { name: 'Movie.mp4', progress: 75, status: 'downloading' },
                { name: 'Series S01E01.mkv', progress: 100, status: 'completed' },
                { name: 'Album.zip', progress: 30, status: 'paused' }
            ];
            
            container.innerHTML = downloads.map(download => `
                <div class="download-item ${download.status}">
                    <div class="download-info">
                        <div class="download-name">${download.name}</div>
                        <div class="download-status">${download.status}</div>
                    </div>
                    <div class="download-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${download.progress}%"></div>
                        </div>
                        <div class="progress-text">${download.progress}%</div>
                    </div>
                </div>
            `).join('');
            
        } catch (error) {
            container.innerHTML = '<div class="error">Failed to load downloads</div>';
        }
    }
    
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            
            // Show install prompt after a delay
            setTimeout(() => {
                this.showInstallPrompt();
            }, 5000);
        });
        
        // Handle install button click
        document.getElementById('installApp')?.addEventListener('click', () => {
            this.installApp();
        });
        
        // Handle dismiss button click
        document.getElementById('dismissInstall')?.addEventListener('click', () => {
            this.hideInstallPrompt();
        });
    }
    
    showInstallPrompt() {
        if (this.deferredPrompt) {
            const prompt = document.getElementById('installPrompt');
            if (prompt) {
                prompt.style.display = 'block';
            }
        }
    }
    
    hideInstallPrompt() {
        const prompt = document.getElementById('installPrompt');
        if (prompt) {
            prompt.style.display = 'none';
        }
    }
    
    async installApp() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            
            const { outcome } = await this.deferredPrompt.userChoice;
            console.log('Install prompt result:', outcome);
            
            if (outcome === 'accepted') {
                // Track installation
                this.trackInstallation();
            }
            
            this.deferredPrompt = null;
            this.hideInstallPrompt();
        }
    }
    
    async trackInstallation() {
        try {
            await fetch('/api/pwa/install', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                })
            });
        } catch (error) {
            console.error('Failed to track installation:', error);
        }
    }
    
    setupNetworkHandling() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log('Back online');
            this.syncPendingActions();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log('Gone offline');
        });
    }
    
    async syncPendingActions() {
        // Sync any pending actions when back online
        console.log('Syncing pending actions...');
    }
    
    async setupPushNotifications() {
        if ('Notification' in window && 'serviceWorker' in navigator) {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('Push notifications enabled');
                await this.subscribeToPush();
            }
        }
    }
    
    async subscribeToPush() {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY')
            });
            
            // Send subscription to server
            await fetch('/api/pwa/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscription)
            });
            
            console.log('Push subscription successful');
            
        } catch (error) {
            console.error('Push subscription failed:', error);
        }
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
    }
    
    bindEvents() {
        // Menu toggle
        document.getElementById('menuToggle')?.addEventListener('click', () => {
            // Implement menu toggle if needed
        });
        
        // Search toggle
        document.getElementById('searchToggle')?.addEventListener('click', () => {
            const searchBar = document.getElementById('searchBar');
            searchBar?.classList.toggle('active');
        });
        
        // Search input
        document.getElementById('searchInput')?.addEventListener('input', (e) => {
            this.performSearch(e.target.value);
        });
        
        // Filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterContent(btn.dataset.filter);
            });
        });
        
        // Quick actions
        document.getElementById('quickCast')?.addEventListener('click', () => {
            this.showPage('streaming');
        });
        
        document.getElementById('addMedia')?.addEventListener('click', () => {
            this.showAddMediaDialog();
        });
        
        document.getElementById('browseLibrary')?.addEventListener('click', () => {
            this.showPage('library');
        });
        
        // Refresh devices
        document.getElementById('refreshDevices')?.addEventListener('click', () => {
            this.loadStreamingDevices();
        });
        
        // Playback controls
        document.getElementById('playPauseBtn')?.addEventListener('click', () => {
            this.togglePlayback();
        });
        
        // Volume control
        document.getElementById('volumeSlider')?.addEventListener('input', (e) => {
            this.setVolume(e.target.value);
        });
        
        // Settings
        document.getElementById('clearCache')?.addEventListener('click', () => {
            this.clearCache();
        });
        
        // Add download
        document.getElementById('addDownload')?.addEventListener('click', () => {
            this.showAddDownloadDialog();
        });
    }
    
    performSearch(query) {
        console.log('Searching for:', query);
        // Implement search functionality
    }
    
    filterContent(filter) {
        console.log('Filtering by:', filter);
        // Implement content filtering
    }
    
    showAddMediaDialog() {
        // Implement add media dialog
        console.log('Show add media dialog');
    }
    
    togglePlayback() {
        const btn = document.getElementById('playPauseBtn');
        const icon = btn?.querySelector('i');
        
        if (icon?.textContent === '▶️') {
            icon.textContent = '⏸️';
            console.log('Playing');
        } else {
            icon.textContent = '▶️';
            console.log('Paused');
        }
    }
    
    setVolume(volume) {
        console.log('Setting volume to:', volume);
        // Implement volume control
    }
    
    async clearCache() {
        try {
            const cacheNames = await caches.keys();
            await Promise.all(
                cacheNames.map(cacheName => caches.delete(cacheName))
            );
            
            alert('Cache cleared successfully');
        } catch (error) {
            console.error('Failed to clear cache:', error);
            alert('Failed to clear cache');
        }
    }
    
    showAddDownloadDialog() {
        // Implement add download dialog
        console.log('Show add download dialog');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mediaHubMobile = new MediaHubMobile();
});
'''
        
        js_path = self.app_root / "mobile.js"
        with open(js_path, 'w') as f:
            f.write(js_content)


# Standalone PWA manager for testing
if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    pwa_manager = MobilePWAManager()
    
    # Create additional assets
    pwa_manager.create_mobile_css()
    pwa_manager.create_mobile_js()
    
    # Setup Flask routes
    pwa_manager.setup_flask_routes(app)
    
    print("Mobile PWA Manager initialized")
    print("Visit /mobile for the PWA interface")
    
    app.run(host='0.0.0.0', port=8080, debug=True)
