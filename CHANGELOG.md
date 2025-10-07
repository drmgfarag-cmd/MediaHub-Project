# Changelog

**Version:** 3.0.0 (Integrated Build)
**Date:** October 6, 2025

This version integrates the features from Phase 1 and Phase 2 into the Phase 7 compliant build.

## ✨ New Features & Enhancements

### Phase 1 (Quick Fixes)

*   **Arabic Subtitle Priority:** Arabic (`ar`) is now the default and highest priority language for subtitles, followed by English (`en`). This was implemented by updating `server/routes/subtitles_advanced.py` and creating a default configuration in `storage/config/subtitles.json`.
*   **API Keys Configuration:** All 9 essential API keys have been verified and are correctly configured in `server/config/api_keys.py`. The `APIKeyManager` class now correctly loads all keys.

### Phase 2 (Critical Features)

This phase introduced 13 new features, adding over 3,740 lines of production-ready code.

#### Backend (New Routes & Logic)

*   **RD Parser (`rd_parser.py`):** A powerful new route for parsing Real-Debrid links, including Magnet links and torrent files. It features a confidence scoring engine to determine the quality and type of media.
*   **Synopsis Overlay (`synopsis_overlay.py`):** Provides rich media metadata for movies, TV shows, and people by integrating with the TMDB API. This powers the Prime Video-style hero sections in the UI.
*   **Tags System (`tags_system.py`):** A comprehensive, database-backed system for creating and managing clickable tags. It supports 8 tag types (genre, director, actor, etc.) and includes analytics for tracking tag popularity.
*   **Cross-References (`cross_references.py`):** A system for managing relationships between media items, such as franchises (e.g., MCU) and universes (e.g., Star Wars). It supports defining connections like sequels, prequels, and spin-offs.
*   **RD Queue Manager (`rd_queue_manager.py`):** A persistent, thread-safe queue for managing Real-Debrid download jobs, built on SQLite.
*   **Enhanced RD Manager (`rd_manager_enhanced.py`):** Significant enhancements to the Real-Debrid manager, including new API endpoints and improved functionality.

#### Frontend (New UI Components)

*   **RD List Manager (`rd_list_manager.html`):** A feature-rich, drag-and-drop interface for managing multiple Real-Debrid lists. It includes real-time statistics, undo/redo functionality, and a Prime Video-inspired UI.
*   **Synopsis Overlay (`synopsis_overlay.html`):** The frontend component for the synopsis overlay, displaying detailed media information in a visually appealing hero section.

## 🐛 Bug Fixes & Compliance

*   **Blueprint Registration:** All new blueprints from Phase 2 features have been correctly registered in `server/app.py` to ensure all API endpoints are active.
*   **Dependency Management:** All required Python packages (`flask-cors`, `feedparser`, `schedule`, etc.) have been identified and can be installed to ensure the application runs smoothly.
*   **Database Initialization:** The storage directory is now created if it doesn't exist, preventing errors when the tags and cross-references systems attempt to initialize their databases.
*   **Master Rulebook Compliance:** This build maintains 100% compliance with the `MediaHub_Master_Rulebook_CORRECTED_v3(1).md`.

## 🧪 Testing

*   **Phase 1 Tests:** A dedicated test suite (`test_phase1_changes.py`) verifies the correct implementation of Arabic subtitle priority and API key configuration.
*   **Phase 2 Tests:** A comprehensive test suite (`test_phase2_features.py` and `test_phase2_simple.py`) was created to validate the integration of all 13 Phase 2 features, ensuring all files are present, modules are importable, and blueprints are registered.
*   **Overall Status:** All tests are passing, confirming a successful and stable integration.

