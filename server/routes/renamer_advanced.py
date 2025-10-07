from flask import Blueprint, jsonify, request
import os, json, re
from datetime import datetime

renamer_advanced_bp = Blueprint('renamer_advanced', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
RENAMER_CONFIG = os.path.join(STO, 'config', 'renamer_patterns.json')

# Illegal characters for different platforms
ILLEGAL_CHARS = {
    'windows': r'[<>:"/\\|?*]',
    'unix': r'/',
    'macos': r'[:/]',
    'universal': r'[<>:"/\\|?*]'
}

