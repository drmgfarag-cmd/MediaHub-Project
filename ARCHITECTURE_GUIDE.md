# MediaHub Architecture Guide

**Version:** 1.0  
**Date:** October 6, 2025  
**Author:** Manus AI Agent

---

## 1. Overview

This document clarifies the hybrid architecture of the MediaHub application, which combines a robust **PyQt6 desktop framework** with a flexible **Flask-powered web UI**. This approach was chosen to satisfy the Master Rulebook's requirement for **"PyQt6 robustness with Prime UI aesthetics."**

This is **NOT a public web application**. It is a desktop application that uses modern web technologies for its user interface, served locally.

---

## 2. Architectural Model: Hybrid Desktop Application

The MediaHub application operates on a hybrid model:

1.  **PyQt6 Main Application Shell:** The core application is a native desktop program built with PyQt6. This handles window management, system tray integration, native dialogs, and core application lifecycle.

2.  **Flask Backend Server:** A Flask web server runs in the background as a separate thread. Its sole purpose is to provide a RESTful API for the frontend. It is only accessible on the local machine (`localhost`).

3.  **Web-based Frontend UI:** The user interface is built with modern web technologies (HTML, CSS, JavaScript, and the React framework). This allows for a fluid, modern, and easily-updatable UI, fulfilling the "Prime UI aesthetics" requirement.

4.  **QWebEngineView Integration:** The web-based UI is loaded and displayed within a `QWebEngineView` widget inside the main PyQt6 window. This Qt widget is a full-featured web browser based on Chromium, allowing seamless integration of the web frontend into the native desktop shell.

### How It Works

1.  The user launches `main_launcher.py`.
2.  The PyQt6 application starts, creating the main window.
3.  In a background thread, the `run_server.py` script starts the Flask API server, binding it to `localhost`.
4.  The PyQt6 main window creates a `QWebEngineView` and directs it to navigate to the local Flask server's address (e.g., `http://localhost:5000`).
5.  The web UI (React frontend) loads inside the `QWebEngineView`.
6.  The web UI makes API calls to the local Flask server to fetch data and perform actions.
7.  The Flask server interacts with the database, external services, and the core application logic.

This model provides the best of both worlds: the stability, performance, and system integration of a native desktop application (PyQt6) with the rich, modern, and flexible user experience of a web application.

---

## 3. Architecture Diagram

```mermaid
graph TD
    subgraph "User's Machine"
        subgraph "PyQt6 Desktop Application (main_launcher.py)"
            A[Main Window] --> B{QWebEngineView (Browser)};
        end

        subgraph "Flask Backend (run_server.py)"
            direction LR
            C[API Endpoints] <--> D[Business Logic];
            D <--> E[Database];
            D <--> F[External Services];
        end

        B -- HTTP Requests --> C;
        C -- JSON Responses --> B;
    end

    style A fill:#cde4ff
    style B fill:#cde4ff
    style C fill:#d5e8d4
    style D fill:#d5e8d4
    style E fill:#f8cecc
    style F fill:#f8cecc
```

**Diagram Explanation:**

-   The **PyQt6 Application** is the native container.
-   The **QWebEngineView** acts as the screen, rendering the UI.
-   The **Flask Backend** runs locally, serving the UI and providing the API.
-   All communication happens locally on the user's machine.

---

## 4. Compliance with Master Rulebook

This hybrid architecture directly addresses and resolves the apparent conflict in the Master Rulebook:

### "NO WEB DEPLOYMENT" Rule

**Compliance:** ✅ PASS

-   The application is **not deployed to a public web server**.
-   The Flask server is only accessible on `localhost`.
-   It is a **desktop application**, not a website. The use of web technologies is an implementation detail for the UI layer.

### "PyQt6 Robustness with Prime UI Aesthetics" Rule

**Compliance:** ✅ PASS

-   **PyQt6 Robustness:** Achieved through the native desktop shell, which handles core application functions and provides stability.
-   **Prime UI Aesthetics:** Achieved through the web-based frontend, which allows for a modern, flexible, and visually appealing user experience that is difficult to achieve with traditional desktop widgets.

### "OFFLINE-FIRST MANDATE" Rule

**Compliance:** ✅ PASS

-   The entire application (PyQt6 shell, Flask server, and web UI files) is bundled together.
-   It can be run completely offline.
-   Online features (like casting or fetching metadata) are progressive enhancements that do not break the core offline functionality.

---

## 5. Conclusion

The hybrid architecture is an intentional and compliant design choice that fulfills all stated requirements in the Master Rulebook. It leverages the strengths of both native desktop and modern web technologies to deliver a superior user experience while remaining a secure, offline-first, desktop application.

This document serves as the official clarification of the MediaHub architecture. All future development and audits should reference this guide.

