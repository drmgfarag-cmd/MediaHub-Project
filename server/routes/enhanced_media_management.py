"""
Phase 2: Enhanced Media Management & Real-Debrid Integration
Implements advanced media library management, metadata integration, and enhanced Real-Debrid features
"""

from flask import Blueprint, request, jsonify, send_file
import os
import json
import sqlite3
import requests
import hashlib
from datetime import datetime, timedelta
import threading
import time
from pathlib import Path

enhanced_media_bp = Blueprint('enhanced_media', __name__)

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
MEDIA_DB = os.path.join(STORAGE, 'enhanced_media.db')
METADATA_CACHE = os.path.join(STORAGE, 'metadata_cache.json')
RD_CACHE = os.path.join(STORAGE, 'rd_enhanced_cache.json')

