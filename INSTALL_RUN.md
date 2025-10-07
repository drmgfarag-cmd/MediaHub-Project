
# MediaHub v67.88 Consolidated — Consolidated

## Quick Start
- **Windows**: double-click `FIRST_RUN.cmd` once, then `RUN_SERVER.cmd` (keeps console open for debugging).
- **Linux/macOS**: run `./FIRST_RUN.sh`, then `./RUN_SERVER.sh`.

Open the printed URL in your browser (default Flask host/port). Logs stream to `storage/logs/app.log` and can be tailed in **Tools → System & Logs** (toggle overlay via **Alt+L**).

## Post-Install
1. Tools → **Dependencies**: set **FFmpeg** and **7-Zip** paths (use placeholders in `/tools/*` if needed).
2. Tools → **Backup & Restore**: make an initial **Snapshot**.
3. Tools → **Accessibility**: enable **High-contrast** or **RTL** if desired.
4. Tools → **Readers & Audio**: choose reader defaults.

## No code edits required
Every feature is accessible via menus, dialogs, or toggles. All feature flags live in `storage/config.json`, `storage/ui_rails.json`, and related JSONs.

## Contents
See `storage/manifest_v67_88.json` for the full feature list consolidated from Phases 1–5.
