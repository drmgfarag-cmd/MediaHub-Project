
## UI Ground Rules (Extensions)

- Persistent views (Sort/Filters/View) per page; density & theme persisted.
- Keyboard-first UX: Command Palette (Ctrl/Cmd+K), Quick Actions (Ctrl/Cmd+J), Esc closes overlays, ? shows help.
- Right-click context menus on cards/rows.
- Drag & drop ingest (RD/Downloader), drag to collections, queue reordering.
- Virtualized lists for large grids; smart empty states.
- Hold-to-confirm for destructive actions.
- Sticky mini-player with Cast.
- Saved Quick Action sets (Minimal/Power/UserDefined).
- WCAG 2.2 compliance and theme variants (Dark/Light/High-Contrast).

### Compliance Gates (Stage C)
- Self-Audit checks: endpoints, pages, required files, config warnings.
- Guard Enforcer blocks Go-Live visually if any Self-Audit failure.
- 5× Smoke tests endpoint and CLI wrappers; results exported to Support Pack.

### Stage E (Downloader, Scheduler, Metadata, Subtitles, Organizer)
- Downloader segmented engine (simulated progress), honors speed & concurrency.
- RD add/unrestrict stubs (swap-in provider calls with keys when ready).
- Online Lists Scheduler (daily/weekly) + on-demand Sync.
- Metadata Editor API and UI.
- Subtitles downloader honors AR→EN priority; writes .srt files (ToS-safe stub).
- Organizer plan builder + Trash quarantine endpoint.
- Guard now checks Stage E surfaces.

### Stage F (Containers, Post-Extract, Editor Pro, CI Gates)
- Decrypt containers (DLC/RSDF/CCF) — simulated parser; plug in real libs later.
- Post-extract hooks (simulate now; call 7-Zip/UnRAR when configured).
- Editor Pro popups: Find/Replace/Bookmark/Columns/Regex/Diff with API.
- Collections Smart Rest across categories.
- Manifest Diff and Release Gate endpoint; CI wrapper script included.

### Stage I (RD Exclusions, Queue Item Ops, OPDS, Comics)
- RD Exclusions browser with paste-parse for filenames & infohashes; profile-safe store.
- Downloader per-item priority and pause/resume/remove controls.
- OPDS 1.x read-only feed (Books/Comics) + search endpoint.
- Comics backend: ingest API + rename pattern; Library now includes comics.
- Guard extended to Stage I surfaces.


**Library Roots Update:** Five main library roots: Movies, TV, Books, Comics, Audio/Music.

### UI Tabs & Floating Quick Actions (Ground Rule Addendum)
- Every primary pillar uses a top **Tabs** strip for major functions (minimize overlays).
- Each page has a **Program Options** dropdown in the sub-bar for less-frequent actions.
- A persistent **Floating Quick Actions** button (⚡) toggles context actions without occluding the main window.
- Guard enforces presence of tabs and FAB selectors to block regressions.

### UI Tab Order Standards (Ground Rule)
- **Library:** Browse • Collections • Filters • Settings
- **RD Manager:** Download • Upload • Extract • Exclusions
- **Downloader:** Collect • Queue • Limits • Containers • Settings • Logs
- **Text Editor:** Edit • Tools • Compare

### RD Batch Add (Pre-Dedup)
- `/api/rd/queue/add` applies **Exclusions** (filenames/names/hashes) and infohash parsing **before** queuing downloads.
- Visible in RD Manager → Download tab (“Add batch to Downloader”).

### Downloader Queue Drag-Reorder
- Drag items in Queue list, click **Save Queue Order** → `/api/downloader/queue/reorder`.
- Engine respects updated order in the loop.

### Stage K (Queue UX++, RD Side Panel, Ctrl+K)
- Downloader: per-item **priority slider**, **host/speed** inline, **pause/resume** icons.
- RD Manager: **Parsed Links side panel** with per-link **Include/Exclude**; one-click **Add to queue (pre-dedup)**.
- Command Palette: **Ctrl+K** opens a scoped palette (page actions + global menu).
- Guard: requires **rd_sidepanel**, **prio_slider_hint**, and **ctrlk_bind** selectors.

### IDM-style Action Toolbar (Ground Rule)
- Each program places primary actions (e.g., Start/Pause/Remove/Retry) in a **menu bar** immediately below tabs.
- Inline item controls may exist for convenience, but toolbar is the canonical control surface.
- Guard enforces `dl_toolbar` and `rd_toolbar` presence to block UI regressions.

### Stage M (Merged Views, Link Grabber, Limiters)
- **Queue subtabs:** All / Active / Finished / Link Grabber
- **Link Grabber:** parse text/DLC dump, dedupe vs queue, save/delete packs, add selected packs.
- **Right-click** context menu on queue items; **sliding parse panel** with close/cancel.
- **Limiters:** global speed & max-running, per-host (existing), and **per-item** kbps limit.
- Guard enforces presence of subtabs and slide panel selectors; endpoints are required for release.

### Stage N (JD-style UI parity)
- **Queue table with columns** (Name/Size/Host/Status/Progress/Speed/Added), sortable-ready.
- **Right Properties pane** (rename, destination, pack, tags; force start, reset, move to pack).
- **Bottom Status Bar** (totals/active/speed hint).
- **Context Menu** on queue rows (Pause/Resume/Remove/Force/Reset).
- **Accounts Manager** page (stub, editable); **Captcha** and **Reconnect** settings pages (stubs).
- **Per-host** limit editor API and **per-item** properties update API.

### Stage O (Usability Parity & Friendliness)
- **Multi-select** (Ctrl/Cmd and Shift ranges) + batch actions via properties pane.
- **Column sorting** by header; **quick filter** search field.
- **Packs sidebar** with counts; click to filter (toggle).
- **Clipboard monitor** (permission-based) in Link Grabber; **Validate** checks online/offline via HEAD.
- **Resizable panes**; density toggle; preferences persist in localStorage.

### Stage Q (Containers, Advanced Packagizer, Scheduler, JD Host Sync)
- **Containers Import**: RSDF/CCF parsed from text; DLC flagged as encrypted (bring keys or use external decryptor).
- **Advanced Packagizer**: rules support **enable/disable**, **order**, **regex** conditions (plus host/contains).
- **Scheduler**: time-of-day bandwidth rules (speed limit & max running), applied live by the engine.
- **Mini Speed Graph** on Scheduler page (preview).
- **JD Host Sync**: fetches official JD repo zip (metadata only) and refreshes `jd_hosts.json`.
- **Guard** blocks release if pages/endpoints are missing.

### Stage S (Unified JD-like UX Polish)
- **Program menubar + integrated search** added to Downloader and RD Manager.
- **Column Manager** (show/hide & reorder) for queue table; persists per-user.
- **Per-Pack Destination Drawer** with bulk-apply.
- **Scheduler Presets** page kept (from Stage Q); live **speed sparkline** on Downloads tab.
- **Guard** requires menubar/search and column manager selectors.

### Stage U (JD Classic UI Mode)
- A toggleable **UI Layout**: Prime (default) or **JD Classic**; persisted in `config/ui.json`.
- **Downloader** gains a JD-style toolbar (top) and bottom bar (speed readout + global limit).
- **Settings** adopts a JD-like tree, routing to existing features (Packagizer, Filters, Scheduler, JD Sync).
- Minimal **Accounts**, **Captcha**, **Reconnect** endpoints/pages to keep everything live-only.
- **Guard** enforces presence of JD layout assets and endpoints.

### Stage W (JD Parity — Optional Features)
- Column presets (Minimal / Host Focus / Debug).
- OS integration (safe) for Open File/Folder via /api/os/open, rooted at config/paths.json.
- Link Grabber Online/Offline check via /api/linkgrabber/check.
- DLC decrypt proxy to user endpoint (config/dlc.json) with a Settings panel.
- RD Manager side Include/Exclude lists with paste-to-extract.

### Stage J1–J2 (JD Sidecar + CNL2)
- **Engine selector** (Native/JD) with toolbar badge and Settings control.
- **JD sidecar lifecycle**: install (configurable URL), start/stop, status, logs.
- **CNL2 bridge**: `/api/jd/cnl2/add` posts links to local 9666; Link Grabber routes Add→CNL2 when engine is JD.
- Guard requires sidecar endpoints and CNL2 bridge; Self-Audit shows JD status.

### Stage J3 (JD Accounts/Captcha/Reconnect Wiring)
- Settings → JD adds **Accounts**, **Captcha**, **Reconnect** subtabs.
- Live actions: **Open JD/MyJD**, **Save & Test Captcha key**, **Run Reconnect** command.
- Self‑Audit warns if Engine=JD and these are unconfigured.

### Stage J4 (JD Queue Parity + MyJDownloader)
- **JD RemoteControl adapter**: when enabled, Downloader mirrors JD queue via `/api/jd/remote/queue` and maps Start/Pause/Remove to JD actions.
- **Settings → JD** adds **MyJDownloader** subtab (store creds; embed console). Used when local RemoteControl is not available.
- **Self‑Audit** warns if Engine=JD and neither RemoteControl nor MyJDownloader is configured.

### Stage UXB1 (Behavior‑First for Native)
- Background services with **Quick Toggles**: clipboard monitor, auto-parse, auto-apply rules, auto-add to queue, auto-extract, move finished to library. Stored in `config/toggles.json` and controlled via `/api/toggles`.
- **Context-first**: Options bar at the bottom with Start/Pause/Remove/Pack/Destination/Limit for selected items; right‑click menus across tables.
- RD Manager lists are **collapsed by default**; add items to Include/Exclude from a row **context menu**.
- Guard requires presence of `/api/toggles` and Quick Toggles UI; Self‑Audit will detect missing toggles file.

### Stage UXB2 (IDM/JD Mimic Layout Presets)
- **Downloader layouts:** Default, **IDM Classic**, **JD Classic**. Switch via **View → Layout**; persisted at `config/ui.json` through `/api/ui/layout`.
- 3‑pane Downloader: **Packages tree** (left), **Queue table** (center), **Properties** (right), with a **status bar** (speed/running/queue/finished) and a Speed Limit shortcut.
- Packages group by **Pack** (if present) else **Host**; click to filter. Context menus and quick toggles remain.

### Stage UXB3 (Tighten UI)
- **Default layout:** IDM Classic; **Density:** Compact; **Mini status bar:** enabled.
- **View → Density:** Comfortable / Compact; **Toggle Mini Status Bar**.
- CSS tightened for buttons, inputs, table rows, and Quick Toggles.

### Stage UXB4 (Docked Quick Toggles)
- Quick Toggles are **docked into the top toolbar** by default; floating tray hidden. 
- Preference lives in `config/ui.json` and is controlled via `/api/ui/density` (`toggles_docked`: true/false).
- View → Density adds **Dock/Undock Quick Toggles**.

### Stage UXB5 (Dock strip across RD Manager & Link Grabber)
- **RD Manager:** docked Quick Toggles in the top toolbar (mirrors Downloader strip).
- **Link Grabber:** dock strip is shared (Downloader toolbar); shows a small **LG** badge when active.

### Stage UXB6 (Editor Docked Behaviors)
- **Text Editor** now has a docked quick‑toggle strip: **Auto‑Save, Trim WS, EOL convert, Tabs↔Spaces, Show Invisibles, Word Wrap**.
- Toggles persist in `config/toggles.json` (keys: `editor_*`) and are wired to background actions on save.

### v49 (A1–A5)
- Command Palette (Ctrl+K) with searchable actions
- Smart Defaults + one-click Best Practice reset
- Limiters API + quick prompt (speed, connections per host)
- Clipboard Rules (junk discard, pack-by-host)
- Session Journal + inline Undo for removes

### v50 (A6–A10)
- First-Run Checklist banner on Hub (RD token, toggles)
- Health Pills (NET/DISK/RD)
- Context Templates menu with /api/templates
- Support Pack button + /api/support/pack
- Toasts + Undo retained

### v51 (B1–B3)
- Segmented downloader config `/api/engine` (connections per file/host/global).
- Link Normalizer `/api/normalize` (strip trackers, force HTTPS) applied on paste/monitor.
- Pack Analyzer `/api/packs/stats` (double‑click Packages tree).

### v52 (B4–B6)
- Auto‑Rules `/api/auto_rules` applied on incoming links.
- Scheduler profiles `/api/schedule` adjust global speed by time windows.
- File Watchers config `/api/watchers` (polling model).

### v53 (B7–B9)
- Hash Index Service endpoints: `/api/hash/config`, `/api/hash/reindex`.
- Library Fast Filters chips on Hub (type‑ahead buttons).
- Inline trailer mini‑player (hero helper `playHeroTrailer(url)`).

### v54 (C1–C3)
- Recordable Macros `/api/macros` + Start/Play from Downloader menu.
- Action Pipelines `/api/pipelines` (define steps).
- Headless Mode toggle `/api/headless` (runs services without UI).

### v55 (C4–C7)
- Per‑collection Rules `/api/collection_rules`.
- Desktop Notifications (permissioned) for key events.
- Compliance/Safe Mode `/api/safe_mode` (disables risky automations).
- Performance Budgeter `/api/perf` (CPU budget, table virtualization).

### v56 (D1–D5)
- Predictive Prefetch `/api/prefetch` + background loop hook.
- Heuristic Retry `/api/retry` policy (per error type).
- Conflict Resolver bottom sheet.
- Cross‑device Profiles export/import `/api/profiles/export|import`.
- Structured Logs toggle `/api/logging`.
