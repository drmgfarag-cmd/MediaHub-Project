# MediaHub Installation Guide

**Version:** 5.4  
**Last Updated:** October 6, 2025

---

## 1. Introduction

This guide provides step-by-step instructions for installing and configuring MediaHub on your system. MediaHub is a hybrid desktop and web application, so installation involves both a desktop component and a local web server.

---

## 2. System Requirements

### Minimum Requirements
- **OS:** Windows 10, macOS 10.15+, or Ubuntu 20.04+
- **CPU:** 2-core 2.0 GHz
- **RAM:** 4 GB
- **Storage:** 500 MB free space
- **Python:** 3.11+

### Recommended Requirements
- **OS:** Windows 11, macOS 12+, or Ubuntu 22.04+
- **CPU:** 4-core 3.0 GHz
- **RAM:** 8 GB
- **Storage:** 1 GB SSD
- **Python:** 3.11+

---

## 3. Installation Steps

### Step 1: Extract the Application

First, extract the `MediaHub_v5.4_FINAL.zip` package to your desired location.

```bash
unzip MediaHub_v5.4_FINAL.zip
cd MediaHub_FINAL_INTEGRATED
```

### Step 2: Install Dependencies

MediaHub requires several Python packages. Install them using `pip3`:

```bash
pip3 install flask flask-cors flask-socketio requests feedparser \
             python-socketio bencode.py guessit schedule pyperclip \
             pycryptodome qrcode pychromecast PyQt6 psutil PyMuPDF \
             ebooklib mutagen tinytag
```

### Step 3: Configure API Keys

MediaHub uses several external services that require API keys. You need to create a `config/api_keys.json` file. An example is provided in `.env.example`.

1. **Create the config directory:**
   ```bash
   mkdir -p config
   ```

2. **Create the `api_keys.json` file:**
   ```bash
   cp .env.example config/api_keys.json
   ```

3. **Edit `config/api_keys.json`** and add your API keys for services like TMDB, Trakt, etc.

### Step 4: Configure Subtitle Settings

Create a `config/subtitles_config.json` file to configure subtitle download preferences.

```bash
cp config/subtitles_config.json.example config/subtitles_config.json
```

Edit the file to set your preferred languages and other options.

---

## 4. Running MediaHub

Once installation is complete, you can start MediaHub using the main launcher script:

```bash
python3.11 main_launcher.py
```

This will:
1. Start the **PyQt6 desktop application**.
2. Start the **local Flask web server** on `http://localhost:5000`.

---

## 5. Accessing MediaHub

### Desktop App
- The native PyQt6 application will launch automatically.

### Web UI
- Open your web browser and navigate to `http://localhost:5000`.

### Mobile/TV
- Find your computer's local IP address (e.g., 192.168.1.100).
- On your mobile device or smart TV, navigate to `http://<your-ip>:5000`.

---

## 6. Troubleshooting

### Installation Issues
- **`pip3` command not found:** Ensure Python 3.11+ is installed and in your system PATH.
- **Dependency errors:** Try installing packages one by one to identify the issue.

### Runtime Errors
- **"Address already in use":** Another application is using port 5000. Stop the other application or change the port in `config/settings.json`.
- **API errors:** Double-check your API keys in `config/api_keys.json`.

For more detailed troubleshooting, see `TROUBLESHOOTING.md`.

---

## 7. Updating MediaHub

To update MediaHub, simply replace the application files with the new version. Your configuration files in the `config/` directory will be preserved.

---

Enjoy using MediaHub!
