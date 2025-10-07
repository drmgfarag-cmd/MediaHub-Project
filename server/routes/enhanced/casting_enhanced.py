"""
Enhanced Casting Functionality with WebOS LG TV Support
"""

import os
import sys
import json
import time
import threading
from flask import Blueprint, request, jsonify, current_app
try:
    from pywebostv.connection import WebOSClient as WebOsClient
    from pywebostv.controls import MediaControl, SystemControl
    WEBOS_AVAILABLE = True
except ImportError:
    # Fallback if pywebostv is not available or has different API
    WEBOS_AVAILABLE = False
    WebOsClient = None
    MediaControl = None
    SystemControl = None

bp = Blueprint("casting_enhanced", __name__)

class CastingManager:
    """Manages casting to different devices, including WebOS LG TVs"""

    def __init__(self, db_connection, db_lock):
        self.db_connection = db_connection
        self.db_lock = db_lock
        self.clients = {}

    def discover_devices(self):
        """Discover all available casting devices on the network"""
        # Placeholder for discovery logic (e.g., using SSDP, mDNS)
        return [{"name": "LG WebOS TV", "type": "webos", "ip": "192.168.1.10"}]

    def cast_to_device(self, device_info, media_url):
        """Cast media to a specific device"""
        device_type = device_info.get("type")
        if device_type == "webos":
            return self._cast_to_webos(device_info, media_url)
        else:
            return {"success": False, "error": "Unsupported device type"}

    def _cast_to_webos(self, device_info, media_url):
        """Cast media to a WebOS LG TV"""
        ip = device_info.get("ip")
        if not ip:
            return {"success": False, "error": "Missing IP address for WebOS device"}

        try:
            client = WebOsClient(ip)
            client.connect()
            for status in client.register(store={}):
                if status == WebOsClient.PROMPTED:
                    print("Please accept the connection on your LG TV")
                elif status == WebOsClient.REGISTERED:
                    media = MediaControl(client)
                    media.play_media(media_url, "video/mp4")
                    return {"success": True, "message": "Casting to LG WebOS TV"}
            return {"success": False, "error": "Failed to register with LG WebOS TV"}
        except Exception as e:
            return {"success": False, "error": str(e)}

@bp.route("/casting/discover", methods=["GET"])
def discover_devices():
    casting_manager = CastingManager(current_app.config["db_connection"], current_app.config["db_lock"])
    devices = casting_manager.discover_devices()
    return jsonify({"success": True, "devices": devices})

@bp.route("/casting/cast", methods=["POST"])
def cast_to_device():
    data = request.json
    device_info = data.get("device_info")
    media_url = data.get("media_url")
    casting_manager = CastingManager(current_app.config["db_connection"], current_app.config["db_lock"])
    result = casting_manager.cast_to_device(device_info, media_url)
    return jsonify(result)

