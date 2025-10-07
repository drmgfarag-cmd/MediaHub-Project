JD Helper (headless) — what it does
-----------------------------------
1) Tries to ensure Java 17 JRE (Temurin) via winget (or Chocolatey fallback).
2) Downloads JDownloader.jar from the official installer site.
3) Launches JD2 headless and writes logs to jd2_headless.log.
4) Calls auto_pair.py to connect via MyJDownloader (credentials from config\myjd.json).
5) After pairing, use Link Grabber → Import DLC… to add container links.