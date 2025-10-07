# MediaHub API Documentation

**Version:** 5.4  
**Last Updated:** October 6, 2025

---

## 1. Introduction

This document provides a comprehensive overview of the MediaHub Golden Surface APIs. These 39 APIs represent the core functionality of MediaHub and are guaranteed to be stable and supported.

---

## 2. Authentication

All API endpoints are protected and require a valid API key. The API key must be provided in the `X-API-Key` header of each request.

```
X-API-Key: YOUR_API_KEY
```

API keys are managed in the `config/api_keys.json` file.

---

## 3. Four Pillars

### MediaHub Home
- **GET /api/home/hero:** Get hero banner items
- **POST /api/home/hero:** Update hero banner items
- **GET /api/home/carousels:** Get content carousels
- **POST /api/home/carousels:** Update content carousels
- **GET /api/home/subcategories:** Get media subcategories
- **POST /api/home/subcategories:** Update media subcategories
- **GET /api/search/omnibox:** Global search

### Text Editor
- **GET /api/editor/documents:** List all documents
- **POST /api/editor/documents:** Create or update a document
- **GET /api/editor/syntax:** Get supported syntax languages
- **GET /api/editor/macros:** List all macros
- **POST /api/editor/macros:** Create or update a macro
- **GET /api/editor/bookmarks:** List all bookmarks
- **POST /api/editor/bookmarks:** Create or update a bookmark

### Downloader
- **GET /api/downloader/queue:** Get download queue
- **POST /api/downloader/add:** Add item to download queue
- **DELETE /api/downloader/queue/{id}:** Remove item from queue
- **GET /api/downloader/status:** Get downloader status
- **POST /api/downloader/extract:** Start archive extraction

### Real-Debrid Manager
- **GET /api/rd/manager/browse:** Browse RD files
- **POST /api/rd/manager/bulk:** Perform bulk operations
- **GET /api/rd/manager/filters:** Get RD filters
- **POST /api/rd/manager/filters:** Update RD filters

---

## 4. Advanced Deduplication

- **GET /api/dedupe/hash_index:** Get hash index status
- **POST /api/dedupe/hash_index:** Rebuild hash index
- **POST /api/dedupe/criteria_analysis:** Analyze duplicates based on criteria
- **POST /api/dedupe/bulk_action:** Perform bulk actions on duplicates
- **GET /api/dedupe/criteria_config:** Get deduplication criteria
- **POST /api/dedupe/criteria_config:** Update deduplication criteria
- **GET /api/dedupe/policy:** Get deduplication policy
- **POST /api/dedupe/policy:** Update deduplication policy
- **POST /api/dedupe/movie_list_resolve:** Resolve duplicates in a movie list

---

## 5. Media Management

- **GET /api/rd/filters/config:** Get RD filters configuration
- **POST /api/rd/filters/config:** Update RD filters configuration
- **GET /api/rss/filters/config:** Get RSS filters configuration
- **POST /api/rss/filters/config:** Update RSS filters configuration
- **GET /api/providers/profiles:** Get metadata provider profiles
- **POST /api/providers/profiles:** Update metadata provider profiles
- **GET /api/subs/policy:** Get subtitle download policy
- **POST /api/subs/policy:** Update subtitle download policy
- **GET /api/collections/manage:** Get all collections
- **POST /api/collections/manage:** Create a new collection
- **PUT /api/collections/manage/{id}:** Update a collection
- **DELETE /api/collections/manage/{id}:** Delete a collection
- **POST /api/metadata/fetch:** Fetch metadata for a media item

---

## 6. Core Infrastructure

- **GET /integrations/status:** Get status of all integrations
- **GET /api/health/comprehensive:** Get comprehensive system health

---

## 7. UI/UX

- **GET /api/ui/locale:** Get current UI locale settings
- **POST /api/ui/locale:** Update UI locale settings
- **POST /api/streaming/hls:** Start an HLS streaming session
- **GET /api/streaming/hls/{id}:** Get HLS stream status
- **DELETE /api/streaming/hls/{id}:** Stop an HLS streaming session

---

## 8. Data Structures

### Media Item
```json
{
  "id": "tt1234567",
  "title": "Example Movie",
  "year": 2025,
  "type": "movie",
  "rating": 8.5,
  "genres": ["Action", "Sci-Fi"],
  "poster": "https://example.com/poster.jpg",
  "backdrop": "https://example.com/backdrop.jpg"
}
```

### Collection
```json
{
  "id": "coll_123",
  "name": "My Favorite Movies",
  "type": "manual",
  "items": ["tt1234567", "tt7654321"]
}
```

---

This documentation provides a high-level overview. For detailed request/response schemas, please refer to the OpenAPI/Swagger specification (coming soon).

