# MediaHub Project

**All-in-One Personal Media Management Platform**

[![GitHub](https://img.shields.io/badge/GitHub-MediaHub--Project-blue)](https://github.com/drmgfarag-cmd/MediaHub-Project)
[![Version](https://img.shields.io/badge/version-5.7--baseline-orange)](https://github.com/drmgfarag-cmd/MediaHub-Project/releases)
[![Status](https://img.shields.io/badge/status-in--development-yellow)](https://github.com/drmgfarag-cmd/MediaHub-Project/projects)

---

## 🎯 Project Overview

MediaHub is a comprehensive personal media management platform that combines the best features of Plex, Jellyfin, JDownloader, FileBot, and more into a single, offline-first application with enterprise-level capabilities.

### Key Features

**Media Management:**
- 📺 Movies & TV Shows
- 📚 Ebooks (EPUB, MOBI, PDF)
- 📖 Comics (CBR, CBZ, CB7)
- 🎵 Audio & Music
- 🎧 Audiobooks
- 📷 Photos
- 📰 Magazines

**Advanced Capabilities:**
- 🎬 Real-Debrid integration
- 📥 Advanced downloader (JDownloader-style)
- 🏷️ Intelligent file organizer (FileBot-style)
- 📡 RSS automation
- 🔍 Advanced search & discovery
- 📊 Collections & smart playlists
- 📱 Mobile streaming
- 📺 TV casting (Chromecast, AirPlay, DLNA, WebOS)
- 🎨 Prime Video-style hero immersion UI

---

## 🚀 Current Status

**Version:** 5.7 (Baseline)  
**Phase:** Pre-Implementation  
**Branch:** `implementation-plan-v1`

### What's Working
- ✅ Backend infrastructure (Flask)
- ✅ Frontend components (React)
- ✅ 176 route files created
- ✅ Tree hierarchy navigation
- ✅ Hero section UI
- ✅ Context menu component

### What Needs Work
- ⚠️ **148 routes not registered** in app.py (80% of features inaccessible)
- ⚠️ UI components not integrated
- ⚠️ Missing features: pinning, collections, multi-select
- ⚠️ No casting UI
- ⚠️ No quality selection UI

---

## 📋 Implementation Plan

Following the **Bulletproof Implementation Plan** to prevent feature regression.

### Phase 0: Setup & Inventory ✅ COMPLETE
- [x] Feature inventory created
- [x] Git repository initialized
- [x] Baseline commit created
- [x] Testing framework designed

### Phase 1: Register All Routes (Days 2-3)
- [ ] Register 148 unregistered routes in batches
- [ ] Test after each batch
- [ ] Commit after each success

### Phase 2: UI Integration (Days 4-8)
- [ ] Context menus on all cards
- [ ] Multi-select and bulk operations
- [ ] Clickable metadata

### Phase 3: New Features (Days 9-15)
- [ ] Pinning system
- [ ] Collections management
- [ ] Casting UI
- [ ] Streaming quality UI

### Phase 4: Polish & Optimization (Days 16-20)
- [ ] Visual timeline
- [ ] WebOS TV enhancements
- [ ] Performance optimization
- [ ] Bug fixes

**Total Timeline:** 20 days (4 weeks)

---

## 🛠️ Technology Stack

**Backend:**
- Python 3.11
- Flask
- SQLite
- FFmpeg

**Frontend:**
- React 19.1.0
- Tailwind CSS
- Radix UI
- Lucide Icons

**Tools:**
- Real-Debrid API
- TMDb API
- IMDb integration
- Trakt integration

---

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- FFmpeg
- 7-Zip (for archive extraction)

### Quick Start

```bash
# Clone repository
git clone https://github.com/drmgfarag-cmd/MediaHub-Project.git
cd MediaHub-Project

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd mediahub-frontend
npm install
cd ..

# Run server
python server/app.py

# Run frontend (in separate terminal)
cd mediahub-frontend
npm run dev
```

### Configuration

1. Copy `config/config.example.json` to `config/config.json`
2. Add your API keys:
   - Real-Debrid API key
   - TMDb API key
   - Trakt API credentials (optional)
3. Configure library paths
4. Start the application

---

## 📚 Documentation

- [Bulletproof Implementation Plan](docs/MediaHub_BULLETPROOF_Implementation_Plan.md)
- [Full Audit Report](docs/MediaHub_Full_Audit_Report.md)
- [Missing Features](docs/MediaHub_Missing_Features_Addendum.md)
- [UI Features](docs/MediaHub_UI_Features_Addendum.md)
- [Extended Research](docs/MediaHub_Extended_Research_Complete.md)
- [User Guide](USER_GUIDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

---

## 🎯 Project Goals

### Short-term (4 weeks)
- ✅ Register all 148 routes
- ✅ Integrate UI components
- ✅ Add pinning, collections, casting UI
- ✅ Zero feature regressions

### Medium-term (8-12 weeks)
- ✅ Visual timeline
- ✅ Advanced automation (ARR stack integration)
- ✅ Enhanced WebOS TV support
- ✅ Performance optimization

### Long-term (3-6 months)
- ✅ Mobile apps (iOS/Android)
- ✅ Plugin system
- ✅ Advanced AI features (recommendations, auto-tagging)
- ✅ Multi-user support (optional)

---

## 🤝 Contributing

This is a personal project, but contributions are welcome!

### Development Workflow

1. Create feature branch from `implementation-plan-v1`
2. Make changes
3. Test thoroughly
4. Commit with descriptive message
5. Create pull request

### Commit Message Format

```
TYPE: Brief description

Detailed description if needed

- Change 1
- Change 2
```

**Types:**
- `FEATURE:` New feature
- `FIX:` Bug fix
- `ROUTES:` Route registration
- `UI:` UI changes
- `DOCS:` Documentation
- `TEST:` Tests
- `REFACTOR:` Code refactoring

---

## 📊 Project Statistics

**Code:**
- 418 Python files
- 30,472 JavaScript files
- 176 route files
- 118 HTML files
- 68,446 total files

**Features:**
- 148 backend routes (to be registered)
- 12 media types supported
- 63 competitor applications researched
- 79 UI screenshots analyzed

---

## 🔒 Privacy & Security

- **Offline-first:** Works completely offline
- **No telemetry:** Zero data collection
- **No accounts:** Single-user, no authentication
- **Local storage:** All data stays on your machine
- **Optional online:** Only for Real-Debrid, metadata, downloads

---

## 📄 License

This project is private and for personal use.

---

## 🙏 Acknowledgments

**Inspired by:**
- Plex & Jellyfin (media management)
- JDownloader (downloading)
- FileBot (file organization)
- Calibre (ebook management)
- YACReader (comic reading)
- Kodi (media center)

**Research:**
- 63 applications analyzed
- 79 UI screenshots studied
- Community feedback incorporated

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue on GitHub
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review the [User Guide](USER_GUIDE.md)

---

## 🗺️ Roadmap

See [GitHub Projects](https://github.com/drmgfarag-cmd/MediaHub-Project/projects) for detailed roadmap and progress tracking.

---

**Built with ❤️ for personal media management**

**Version:** 5.7-baseline  
**Last Updated:** October 7, 2025  
**Status:** Active Development
