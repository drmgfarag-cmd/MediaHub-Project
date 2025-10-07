# 📖 MediaHub Master Rulebook v3.0 (CORRECTED with User Clarifications)

_Date: October 5, 2025 — Authoritative rulebook with user corrections integrated_

---

## 🚨 **SUPREME RULE #0 (NEVER VIOLATE - USER CLARIFIED):**

**COMPLETE DELIVERY MANDATE:** Every build MUST be delivered complete, live, fully integrated, implemented and functional with proper working API, frontend and backend. NO drops, NO stubs, NO deltas, NO regression. Always build over the last most completed build to preserve all features. **NO FEATURE IS REMOVED UNLESS REPLACED BY ONE WITH EQUAL OR BETTER VALUE.**

**PROGRESSIVE BUILD MANDATE:** Your base build shall be the last most feature complete build and every phase or plan implementation you will give a complete build based on the last one (progressive builds so to avoid feature loss).

---

## 1. **Golden Principles (USER CORRECTED)**

### **🚨 CORE MANDATES:**
1. **No-drops:** Nothing gets removed. Any change must be equal or better.  
2. **Behavior-first:** UI is disabled or blocked unless backend/config is healthy.  
3. **Guard-gated:** `/api/rules_audit` + Guard banner must block "Go Live" if any Golden Surface is missing.  
4. **Single complete build:** Always ship as one archive, runnable offline on first launch.  
5. **Determinism:** Same inputs → same outputs. Pin dependencies, keep presets.  
6. **Security:** No secrets in code/logs. Tokens read from env/config only. Support Pack redacts them.  
7. **🆕 OFFLINE-FIRST MANDATE:** Personal build at enterprise level. Mainly offline project allowing online accessibility for features requiring it **WITHOUT DROPPING ANY FEATURE**.
8. **🆕 HYBRID ARCHITECTURE:** PyQt6 desktop app with local web server for TV/mobile streaming and casting. **NO PUBLIC INTERNET DEPLOYMENT** - local network only.
9. **🆕 PROGRESSIVE ENHANCEMENT:** Every build must exceed the previous most complete version. Never start from scratch.
10. **🆕 ENTERPRISE PERSONAL BUILD:** Keep pre-configured keys, maintain enterprise-level quality.
11. **🆕 CONFLICT RESOLUTION:** Flag conflicts for user approval - do not make assumptions.

### **🆕 REMOVED REQUIREMENTS (USER SPECIFIED):**
- ~~Scene group priority~~ - **REMOVED FROM RULES** per user directive

---

## 2. **Architecture & Implementation Standards (USER CLARIFIED - UPDATED OCT 6, 2025)**

### **Platform Requirements:**
- **Primary:** PyQt6 Desktop Application (robust implementation)
- **UI Aesthetics:** Prime Video-style interface (aesthetic view)
- **Integration Approach:** Combine Golden Surfaces robustness with Prime UI aesthetics for best results
- **Deployment:** **HYBRID ARCHITECTURE** - PyQt6 desktop app with local web server for streaming/casting features

### **🆕 HYBRID ARCHITECTURE SPECIFICATION (Oct 6, 2025):**
- **Desktop Application:** PyQt6 native application as primary interface
- **Local Web Server:** Flask backend for API services
- **Web UI Access:** Local web interface accessible for:
  - **TV Streaming:** WebOS, Roku, Smart TV browsers
  - **Mobile Streaming:** iOS, Android browsers
  - **Casting:** Chromecast, DLNA devices
  - **Remote Access:** Local network only (no public internet deployment)
- **Offline-First:** All core features work offline; streaming/casting require local network
- **No Public Deployment:** Web server binds to localhost/LAN only, never exposed to public internet

### **Feature Completeness Standards:**
- **Complete Filtering System:** If implemented, keep with scoring system
- **Automatic Subtitle Downloader:** Implemented in organizer part of media library
- **All Features Preserved:** No feature removal unless replaced by equal/better value
- **Pre-configured Keys:** Maintain enterprise-level pre-configuration

---

## 3. **Golden Surfaces (UPDATED - NO SCENE GROUP PRIORITY)**

### **Core Infrastructure APIs**
- `/api/guard/scan`  
- `/integrations/status`  
- `/api/selftest/run`  
- `/api/support/pack`  
- `/api/rules_audit`  
- `/api/health/comprehensive` - Full system health check
- `/api/foundation/verify` - Verify build foundation integrity

### **Media Management APIs**
- `/api/rd/filters/config`  
- `/api/rss/filters/config`  
- `/api/providers/profiles`  
- `/api/dedupe/policy`  
- `/api/dedupe/movie_list_resolve`  
- `/api/dedupe/hash_index`  
- `/api/subs/policy`  
- `/api/media/organize` - FileBot-style media organization **WITH AUTOMATIC SUBTITLE DOWNLOADER**
- `/api/collections/manage` - Dynamic collection creation and management
- `/api/metadata/fetch` - Multi-provider metadata fetching

### **Four Pillars APIs**
#### MediaHub Home (Prime UI Aesthetics)
- `/api/home/hero` - Hero section content management
- `/api/home/carousels` - Content carousel management
- `/api/home/subcategories` - Movies, TV, Books, Audio subcategories
- `/api/search/omnibox` - Advanced global search

#### Text Editor (PyQt6 Robustness)
- `/api/editor/documents` - Multi-document interface management
- `/api/editor/syntax` - Syntax highlighting for 50+ languages
- `/api/editor/macros` - Macro recording/playbook
- `/api/editor/bookmarks` - Document bookmarking

#### Downloader (Combined Best Results)
- `/api/downloader/queue` - JDownloader-style queue management
- `/api/downloader/auto` - RSS automation and quality profiles
- `/api/downloader/extraction` - Archive extraction with nested support

#### Real-Debrid Manager (Enterprise Level)
- `/api/rd/manager/browse` - Browsable RD links interface
- `/api/rd/manager/bulk` - Bulk operations support
- `/api/rd/manager/filters` - **COMPLETE FILTERING SYSTEM WITH SCORING** (if implemented, keep it)

### **UI/UX APIs (Prime UI + PyQt6 Integration)**
- `/api/ui/themes` - Prime Video-style theming with PyQt6 robustness
- `/api/ui/locale` - Arabic/RTL support
- `/api/casting/devices` - WebOS/DLNA device discovery (online feature)
- `/api/streaming/hls` - Local network streaming (online feature)

---

## 4. **Advanced Deduplication System (USER CLARIFIED)**

### **Requirements:**
- **Complete Filtering System with Scoring** - If implemented, KEEP IT
- **No Scene Group Priority** - REMOVED per user directive
- **Multi-Criteria Filtering** - Maintain if present
- **Configurable Scoring Engine** - Preserve existing implementation

### **API Specifications:**
- **POST** `/api/dedupe/hash_index`: append items into `config/hash_index.json`  
- **GET** `/api/dedupe/hash_index`: return grouped dupes with multi-criteria analysis
- **POST** `/api/dedupe/criteria_analysis`: analyze and score content by multiple criteria
- **POST** `/api/dedupe/bulk_action`: execute bulk deduplication with user approval
- **GET** `/api/dedupe/criteria_config`: retrieve current filtering and scoring configuration
- **POST** `/api/dedupe/criteria_config`: update filtering and scoring configuration

---

## 5. **Feature Implementation Requirements (USER CORRECTED)**

### **Must-Have Features (Enterprise Personal Build):**
- Complete filtering system with scoring (if implemented, preserve)
- Prime Video-style UI aesthetics with PyQt6 robustness
- Complete four pillars implementation
- **Automatic subtitle downloader in organizer part of media library**
- FileBot-style media organizer
- WebOS/DLNA casting support (online feature)
- Multi-document text editor with Notepad++ parity
- **Pre-configured keys maintenance**

### **Architecture Integration:**
- **Golden Surfaces + Prime UI:** Combined for best results
- **PyQt6 Robustness:** Maintain desktop application strength
- **Prime UI Aesthetics:** Visual appeal and modern interface
- **No Web Deployment:** Desktop application only

---

## 6. **Progressive Build Workflow (USER MANDATED)**

### **Base Build Selection:**
1. **Foundation:** Use the last most feature complete build as base
2. **NO REGRESSION:** Every new build must exceed the previous version
3. **Feature Preservation:** ALL existing features must be maintained
4. **Enhancement Only:** Add features or improve existing ones

### **Implementation Process:**
1. **Identify Most Complete Build:** Based on feature completeness analysis
2. **Baseline Establishment:** Use complete build as foundation
3. **Progressive Enhancement:** Add/improve features without removing any
4. **Complete Delivery:** Every phase delivers a complete, functional build
5. **Conflict Resolution:** Flag conflicts for user approval

---

## 7. **Quality Assurance (ENTERPRISE LEVEL)**

### **Mandatory Checks:**
- Golden Surfaces 100% coverage
- Four pillars 100% implementation
- UI integration (Prime aesthetics + PyQt6 robustness)
- Complete filtering system with scoring (if implemented)
- Automatic subtitle downloader in media organizer
- Configuration preservation (pre-configured keys)
- **NO WEB DEPLOYMENT** validation
- Progressive enhancement verification

### **User Acceptance Criteria:**
- "Personal build at enterprise level" ✓
- "Mainly offline allowing online features without dropping features" ✓
- "PyQt6 robustness with Prime UI aesthetics" ✓
- "Complete filtering system with scoring" ✓
- "Automatic subtitle downloader in organizer" ✓
- "No web deployment" ✓

---

## 8. **Standards (USER CLARIFIED)**

### **🚨 DELIVERY STANDARDS (MANDATORY - NO DEVIATION):**
- **NEVER deliver incomplete builds** - Every delivery must be 100% functional
- **NEVER deliver stubs or placeholders** - All features must be fully implemented
- **NEVER deliver with regressions** - Each build must exceed the previous version
- **NEVER remove features** - Unless replaced by equal or better value alternatives
- **ALWAYS deliver working APIs** - Frontend AND backend must be fully functional
- **ALWAYS build incrementally** - Use the most complete previous build as foundation
- **ALWAYS preserve functionality** - Every working feature must remain working
- **🆕 NEVER deploy as website** - Desktop PyQt6 application only
- **🆕 ALWAYS maintain enterprise level** - Personal build with enterprise quality
- **🆕 ALWAYS preserve pre-configured keys** - Maintain existing configuration

### **TECHNICAL STANDARDS:**
- Bundle all assets (no CDN dependencies)
- Validate JSON configs strictly
- Import/export APIs return detailed summaries
- No secrets in logs or code
- Every build ships this updated rulebook
- Prime Video-style UI with PyQt6 robustness
- Four pillars completeness verification
- Complete filtering system with scoring preservation

---

## 9. **Adherence & Compliance Protocol (USER EMPHASIZED)**

### **🚨 STRICT ADHERENCE REQUIRED:**
- **NO DEVIATIONS** from these rules (like web deployment)
- **PROGRESSIVE BUILDS ONLY** - Always build on most complete foundation
- **COMPLETE DELIVERY MANDATE** - Every build must be fully functional
- **FEATURE PRESERVATION** - No drops, no stubs, no regression
- **CONFLICT FLAGGING** - Get user approval for any conflicts

### **Implementation Enforcement:**
- These rules MUST be implemented when starting each build/phase/plan
- NO EXCEPTIONS to Supreme Rule #0
- STRICT compliance monitoring and validation
- USER APPROVAL required for any rule conflicts

---

## 10. **Final Build Target (USER SPECIFICATION)**

### **Most Complete Foundation:**
Based on analysis: **MediaHub_Ultimate_Final_v2.0.zip**
- **Feature Completeness:** 92/100 
- **API Endpoints:** 71+ active routes
- **Enterprise Grade:** Production-ready implementation
- **Complete Four Pillars:** All components fully implemented
- **PyQt6 Desktop:** Robust implementation
- **Prime UI Elements:** Aesthetic interface components

### **Progressive Enhancement Target:**
- **Preserve ALL existing features** from Ultimate_Final_v2.0
- **Enhance filtering system** (maintain scoring if implemented)
- **Integrate automatic subtitle downloader** in media organizer
- **Combine PyQt6 robustness with Prime UI aesthetics**
- **Maintain pre-configured enterprise keys**
- **Ensure NO WEB DEPLOYMENT**

---

**Author:** MiniMax Agent  
**Version:** 3.0 (User Corrected & Clarified)  
**Status:** Authoritative Implementation Guide  
**Compliance:** Mandatory - No Deviations Permitted
