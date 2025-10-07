# MediaHub Troubleshooting Guide

**Version:** 5.4  
**Last Updated:** October 6, 2025

---

## 1. Common Issues

This guide provides solutions for common issues you may encounter with MediaHub.

---

## 2. Installation & Startup

### Issue: `pip3` command not found
- **Cause:** Python 3.11+ is not installed or not in your system PATH.
- **Solution:** Install Python 3.11+ and ensure it is added to your system PATH during installation.

### Issue: "Address already in use" on startup
- **Cause:** Another application is using port 5000.
- **Solution:** 
  1. Stop the other application.
  2. **OR** change the port in `config/settings.json` (if it exists) or in the application settings.

### Issue: Missing dependencies
- **Cause:** Required Python packages are not installed.
- **Solution:** Run the installation command again:
  ```bash
  pip3 install -r requirements.txt
  ```

---

## 3. Media & Metadata

### Issue: Media not appearing in library
- **Cause:** Media folders are not configured correctly or have not been scanned.
- **Solution:**
  1. Go to **Settings > Media Folders** and ensure your media directories are added.
  2. Trigger a manual scan by going to **Settings > Media Folders > Scan All**.

### Issue: Incorrect metadata or artwork
- **Cause:** Incorrect match from metadata providers.
- **Solution:**
  1. Right-click on the media item and select **"Fix Match"**.
  2. Manually search for the correct title and year.
  3. Select the correct match from the search results.

### Issue: Subtitles not downloading
- **Cause:** Incorrect subtitle policy configuration or no available subtitles.
- **Solution:**
  1. Go to **Settings > Subtitle Policy** and ensure your preferred languages are configured correctly.
  2. Ensure "Enable Auto-Download" is checked.
  3. Right-click on the media item and select **"Search for Subtitles"** to do a manual search.

---

## 4. Playback & Streaming

### Issue: Video not playing
- **Cause:** Unsupported video format or codec.
- **Solution:** MediaHub uses standard HTML5 video playback. Ensure your media is in a compatible format (e.g., MP4 with H.264 video and AAC audio). MediaHub will attempt to transcode some formats, but this is not guaranteed.

### Issue: Casting not working
- **Cause:** Chromecast device is not on the same network or is not discoverable.
- **Solution:**
  1. Ensure your Chromecast and the device running MediaHub are on the same Wi-Fi network.
  2. Restart your Chromecast device.
  3. Ensure your firewall is not blocking network discovery.

---

## 5. Real-Debrid & Downloads

### Issue: Real-Debrid files not showing
- **Cause:** Incorrect Real-Debrid API key or account issue.
- **Solution:**
  1. Go to **Settings > Integrations** and check the status of Real-Debrid.
  2. Verify your Real-Debrid API key in `config/api_keys.json`.
  3. Check your Real-Debrid account on their website to ensure it is active.

### Issue: Downloads not starting
- **Cause:** Downloader is not configured correctly or there are no available sources.
- **Solution:**
  1. Check the **Downloader** pillar to see the status of the download queue.
  2. Check the logs for any error messages.

---

## 6. Logs & Advanced Troubleshooting

### Log Files
- MediaHub logs are located in the `logs/` directory.
- `app.log`: Main application log.
- `web_server.log`: Flask web server log.

### Rebuilding the Database
If your library is corrupt or you want to start fresh, you can delete the database file (`database.db`) and restart MediaHub. This will trigger a full rescan of your media.

---

## 7. Contact & Support

If you are still experiencing issues, please refer to the official MediaHub documentation or community forums for support.

- **GitHub Issues:** [https://github.com/your-repo/mediahub/issues](https://github.com/your-repo/mediahub/issues)
- **Community Forum:** [https://community.mediahub.com](https://community.mediahub.com)

---

Thank you for using MediaHub!
