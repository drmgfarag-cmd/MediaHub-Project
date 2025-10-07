#!/usr/bin/env python3
"""
WebOS TV Casting Service
Phase 1A Streaming Infrastructure Component

Provides LG Smart TV integration, WebOS application interface,
remote media control, and TV-specific optimizations.
"""

import json
import time
import uuid
import base64
import hashlib
import threading
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import websocket
import requests
from urllib.parse import urljoin


@dataclass
class WebOSDevice:
    """Represents a WebOS TV device"""
    ip_address: str
    name: str
    model: str
    version: str
    port: int = 3000
    secure_port: int = 3001
    client_key: Optional[str] = None
    connected: bool = False
    last_seen: datetime = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.last_seen:
            data['last_seen'] = self.last_seen.isoformat()
        return data


@dataclass
class MediaItem:
    """Represents a media item for casting"""
    url: str
    title: str
    description: str = ""
    icon_url: str = ""
    mime_type: str = "video/mp4"
    duration: Optional[int] = None
    subtitles: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.subtitles is None:
            self.subtitles = []


class WebOSCastingService:
    """WebOS TV casting service for LG Smart TVs"""
    
    def __init__(self):
        self.discovered_tvs: Dict[str, WebOSDevice] = {}
        self.connections: Dict[str, websocket.WebSocket] = {}
        self.connection_threads: Dict[str, threading.Thread] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.request_id_counter = 0
        self.pending_requests: Dict[str, Dict] = {}
        self.pairing_callbacks: Dict[str, Callable] = {}
        
        # WebOS API endpoints
        self.api_endpoints = {
            'system_info': 'ssap://system/getSystemInfo',
            'launch_app': 'ssap://system.launcher/launch',
            'media_play': 'ssap://media.controls/play',
            'media_pause': 'ssap://media.controls/pause',
            'media_stop': 'ssap://media.controls/stop',
            'media_seek': 'ssap://media.controls/seek',
            'volume_up': 'ssap://audio/volumeUp',
            'volume_down': 'ssap://audio/volumeDown',
            'set_volume': 'ssap://audio/setVolume',
            'get_volume': 'ssap://audio/getVolume',
            'mute': 'ssap://audio/setMute',
            'show_toast': 'ssap://system.notifications/createToast',
            'open_url': 'ssap://system.launcher/open'
        }
    
    def discover_webos_tvs(self) -> List[WebOSDevice]:
        """Discover WebOS TVs on the network using SSDP"""
        discovered = []
        
        try:
            import socket
            
            # SSDP discovery for WebOS TVs
            ssdp_request = (
                "M-SEARCH * HTTP/1.1\r\n"
                "HOST: 239.255.255.250:1900\r\n"
                "MAN: \"ssdp:discover\"\r\n"
                "ST: urn:lge-com:service:webos-second-screen:1\r\n"
                "MX: 3\r\n\r\n"
            )
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            
            try:
                sock.sendto(ssdp_request.encode(), ('239.255.255.250', 1900))
                
                start_time = time.time()
                while time.time() - start_time < 10:
                    try:
                        data, addr = sock.recvfrom(4096)
                        response = data.decode('utf-8')
                        
                        if 'webos-second-screen' in response:
                            tv_device = self._parse_webos_ssdp_response(response, addr[0])
                            if tv_device:
                                device_id = f"{tv_device.ip_address}:{tv_device.port}"
                                self.discovered_tvs[device_id] = tv_device
                                discovered.append(tv_device)
                                
                    except socket.timeout:
                        continue
                        
            finally:
                sock.close()
                
        except Exception as e:
            print(f"WebOS discovery error: {e}")
        
        return discovered
    
    def _parse_webos_ssdp_response(self, response: str, ip_address: str) -> Optional[WebOSDevice]:
        """Parse SSDP response for WebOS TV information"""
        try:
            lines = response.split('\r\n')
            location = None
            
            for line in lines:
                if line.upper().startswith('LOCATION:'):
                    location = line.split(':', 1)[1].strip()
                    break
            
            if location:
                # Try to get device info from description XML
                try:
                    device_info = requests.get(location, timeout=5)
                    if device_info.status_code == 200:
                        # Parse basic info - WebOS TVs often have minimal SSDP info
                        return WebOSDevice(
                            ip_address=ip_address,
                            name=f"LG TV ({ip_address})",
                            model="WebOS TV",
                            version="Unknown",
                            last_seen=datetime.now()
                        )
                except Exception:
                    pass
                
                # Fallback to basic device info
                return WebOSDevice(
                    ip_address=ip_address,
                    name=f"LG TV ({ip_address})",
                    model="WebOS TV",
                    version="Unknown",
                    last_seen=datetime.now()
                )
                
        except Exception as e:
            print(f"SSDP response parsing error: {e}")
        
        return None
    
    def connect_to_tv(self, device: WebOSDevice, client_key: str = None) -> bool:
        """Connect to WebOS TV via WebSocket"""
        device_id = f"{device.ip_address}:{device.port}"
        
        if device_id in self.connections and self.connections[device_id]:
            print(f"Already connected to {device.name}")
            return True
        
        try:
            # Use stored client key if available
            if client_key:
                device.client_key = client_key
            
            ws_url = f"ws://{device.ip_address}:{device.port}/"
            
            def on_message(ws, message):
                self._handle_websocket_message(device_id, message)
            
            def on_error(ws, error):
                print(f"WebSocket error for {device.name}: {error}")
                device.connected = False
            
            def on_close(ws, close_status_code, close_msg):
                print(f"WebSocket closed for {device.name}")
                device.connected = False
                if device_id in self.connections:
                    del self.connections[device_id]
            
            def on_open(ws):
                print(f"Connected to {device.name}")
                device.connected = True
                # Send handshake/pairing request
                self._send_handshake(device_id, device)
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            self.connections[device_id] = ws
            
            # Start connection in separate thread
            thread = threading.Thread(
                target=ws.run_forever,
                daemon=True
            )
            self.connection_threads[device_id] = thread
            thread.start()
            
            # Wait a moment for connection to establish
            time.sleep(2)
            
            return device.connected
            
        except Exception as e:
            print(f"Connection error: {e}")
            device.connected = False
            return False
    
    def _send_handshake(self, device_id: str, device: WebOSDevice):
        """Send handshake/pairing request to WebOS TV"""
        try:
            handshake_payload = {
                "type": "register",
                "id": self._get_next_request_id(),
                "payload": {
                    "forcePairing": False,
                    "pairingType": "PROMPT",
                    "manifest": {
                        "manifestVersion": 1,
                        "appId": "com.mediahub.webos",
                        "vendorId": "com.mediahub",
                        "localizedAppNames": {
                            "english": "MediaHub",
                            "korean": "MediaHub",
                            "japanese": "MediaHub"
                        },
                        "localizedVendorNames": {
                            "english": "MediaHub",
                            "korean": "MediaHub",
                            "japanese": "MediaHub"
                        },
                        "permissions": [
                            "LAUNCH",
                            "LAUNCH_WEBAPP",
                            "APP_TO_APP",
                            "CLOSE",
                            "TEST_OPEN",
                            "TEST_PROTECTED",
                            "CONTROL_AUDIO",
                            "CONTROL_DISPLAY",
                            "CONTROL_INPUT_JOYSTICK",
                            "CONTROL_INPUT_MEDIA_RECORDING",
                            "CONTROL_INPUT_MEDIA_PLAYBACK",
                            "CONTROL_INPUT_TV",
                            "CONTROL_POWER",
                            "READ_APP_STATUS",
                            "READ_CURRENT_CHANNEL",
                            "READ_INPUT_DEVICE_LIST",
                            "READ_NETWORK_STATE",
                            "READ_RUNNING_APPS",
                            "READ_TV_CHANNEL_LIST",
                            "WRITE_NOTIFICATION_TOAST",
                            "READ_POWER_STATE",
                            "READ_COUNTRY_INFO"
                        ],
                        "signatures": []
                    }
                }
            }
            
            # Add client key if we have one
            if device.client_key:
                handshake_payload["payload"]["client-key"] = device.client_key
            
            self._send_message(device_id, handshake_payload)
            
        except Exception as e:
            print(f"Handshake error: {e}")
    
    def _handle_websocket_message(self, device_id: str, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            msg_id = data.get('id')
            payload = data.get('payload', {})
            
            if msg_type == 'registered':
                # Store client key for future connections
                client_key = payload.get('client-key')
                if client_key and device_id in self.discovered_tvs:
                    device = list(self.discovered_tvs.values())[0]  # Get device object
                    for dev in self.discovered_tvs.values():
                        if f"{dev.ip_address}:{dev.port}" == device_id:
                            dev.client_key = client_key
                            break
                
                print(f"Successfully paired with TV: {device_id}")
                
                # Notify pairing callback if set
                if device_id in self.pairing_callbacks:
                    self.pairing_callbacks[device_id](True, client_key)
                    del self.pairing_callbacks[device_id]
            
            elif msg_type == 'response':
                # Handle API response
                if msg_id in self.pending_requests:
                    request_info = self.pending_requests[msg_id]
                    callback = request_info.get('callback')
                    if callback:
                        callback(payload)
                    del self.pending_requests[msg_id]
            
            elif msg_type == 'error':
                error_msg = payload.get('error', 'Unknown error')
                print(f"WebOS error: {error_msg}")
                
                if device_id in self.pairing_callbacks:
                    self.pairing_callbacks[device_id](False, error_msg)
                    del self.pairing_callbacks[device_id]
            
        except Exception as e:
            print(f"Message handling error: {e}")
    
    def _send_message(self, device_id: str, message: dict):
        """Send message to WebOS TV"""
        try:
            ws = self.connections.get(device_id)
            if ws and ws.sock and ws.sock.connected:
                ws.send(json.dumps(message))
                return True
        except Exception as e:
            print(f"Send message error: {e}")
        return False
    
    def _get_next_request_id(self) -> str:
        """Generate next request ID"""
        self.request_id_counter += 1
        return str(self.request_id_counter)
    
    def cast_media(self, device_id: str, media: MediaItem) -> bool:
        """Cast media to WebOS TV"""
        try:
            request_id = self._get_next_request_id()
            
            # Launch media player app first
            launch_message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['launch_app'],
                "payload": {
                    "id": "com.webos.app.mediaplayer",
                    "params": {
                        "mediaUrl": media.url,
                        "title": media.title,
                        "description": media.description,
                        "iconUrl": media.icon_url,
                        "mimeType": media.mime_type
                    }
                }
            }
            
            if media.subtitles:
                launch_message["payload"]["params"]["subtitles"] = media.subtitles
            
            return self._send_message(device_id, launch_message)
            
        except Exception as e:
            print(f"Cast media error: {e}")
            return False
    
    def play_media(self, device_id: str) -> bool:
        """Play media on WebOS TV"""
        return self._send_control_command(device_id, 'media_play')
    
    def pause_media(self, device_id: str) -> bool:
        """Pause media on WebOS TV"""
        return self._send_control_command(device_id, 'media_pause')
    
    def stop_media(self, device_id: str) -> bool:
        """Stop media on WebOS TV"""
        return self._send_control_command(device_id, 'media_stop')
    
    def seek_media(self, device_id: str, position: int) -> bool:
        """Seek to position in media (seconds)"""
        try:
            request_id = self._get_next_request_id()
            message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['media_seek'],
                "payload": {
                    "position": position
                }
            }
            return self._send_message(device_id, message)
        except Exception as e:
            print(f"Seek media error: {e}")
            return False
    
    def set_volume(self, device_id: str, volume: int) -> bool:
        """Set volume on WebOS TV (0-100)"""
        try:
            request_id = self._get_next_request_id()
            message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['set_volume'],
                "payload": {
                    "volume": max(0, min(100, volume))
                }
            }
            return self._send_message(device_id, message)
        except Exception as e:
            print(f"Set volume error: {e}")
            return False
    
    def volume_up(self, device_id: str) -> bool:
        """Increase volume on WebOS TV"""
        return self._send_control_command(device_id, 'volume_up')
    
    def volume_down(self, device_id: str) -> bool:
        """Decrease volume on WebOS TV"""
        return self._send_control_command(device_id, 'volume_down')
    
    def mute(self, device_id: str, muted: bool = True) -> bool:
        """Mute/unmute WebOS TV"""
        try:
            request_id = self._get_next_request_id()
            message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['mute'],
                "payload": {
                    "mute": muted
                }
            }
            return self._send_message(device_id, message)
        except Exception as e:
            print(f"Mute error: {e}")
            return False
    
    def show_toast(self, device_id: str, message: str, icon_url: str = None) -> bool:
        """Show toast notification on WebOS TV"""
        try:
            request_id = self._get_next_request_id()
            payload = {
                "message": message
            }
            if icon_url:
                payload["iconUrl"] = icon_url
            
            toast_message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['show_toast'],
                "payload": payload
            }
            return self._send_message(device_id, toast_message)
        except Exception as e:
            print(f"Show toast error: {e}")
            return False
    
    def open_url(self, device_id: str, url: str) -> bool:
        """Open URL in WebOS TV browser"""
        try:
            request_id = self._get_next_request_id()
            message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['open_url'],
                "payload": {
                    "target": url
                }
            }
            return self._send_message(device_id, message)
        except Exception as e:
            print(f"Open URL error: {e}")
            return False
    
    def _send_control_command(self, device_id: str, command: str) -> bool:
        """Send basic control command to WebOS TV"""
        try:
            request_id = self._get_next_request_id()
            message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints[command]
            }
            return self._send_message(device_id, message)
        except Exception as e:
            print(f"Control command error: {e}")
            return False
    
    def get_system_info(self, device_id: str, callback: Callable = None):
        """Get system information from WebOS TV"""
        try:
            request_id = self._get_next_request_id()
            
            if callback:
                self.pending_requests[request_id] = {'callback': callback}
            
            message = {
                "type": "request",
                "id": request_id,
                "uri": self.api_endpoints['system_info']
            }
            return self._send_message(device_id, message)
        except Exception as e:
            print(f"Get system info error: {e}")
            return False
    
    def disconnect_from_tv(self, device_id: str):
        """Disconnect from WebOS TV"""
        try:
            if device_id in self.connections:
                ws = self.connections[device_id]
                if ws:
                    ws.close()
                del self.connections[device_id]
            
            if device_id in self.connection_threads:
                thread = self.connection_threads[device_id]
                if thread.is_alive():
                    thread.join(timeout=5)
                del self.connection_threads[device_id]
            
            # Update device status
            for device in self.discovered_tvs.values():
                if f"{device.ip_address}:{device.port}" == device_id:
                    device.connected = False
                    break
                    
        except Exception as e:
            print(f"Disconnect error: {e}")
    
    def get_connected_devices(self) -> List[Dict]:
        """Get list of connected WebOS devices"""
        connected = []
        for device in self.discovered_tvs.values():
            if device.connected:
                connected.append(device.to_dict())
        return connected
    
    def set_pairing_callback(self, device_id: str, callback: Callable[[bool, str], None]):
        """Set callback for pairing result"""
        self.pairing_callbacks[device_id] = callback


# Standalone service for testing
if __name__ == '__main__':
    def on_pairing_result(success: bool, result: str):
        if success:
            print(f"Pairing successful! Client key: {result}")
        else:
            print(f"Pairing failed: {result}")
    
    service = WebOSCastingService()
    
    # Discover TVs
    print("Discovering WebOS TVs...")
    tvs = service.discover_webos_tvs()
    
    if tvs:
        tv = tvs[0]
        device_id = f"{tv.ip_address}:{tv.port}"
        
        print(f"Found TV: {tv.name} at {tv.ip_address}")
        
        # Set pairing callback
        service.set_pairing_callback(device_id, on_pairing_result)
        
        # Connect to TV
        if service.connect_to_tv(tv):
            print("Connected to TV")
            
            # Wait for pairing
            time.sleep(5)
            
            # Test media casting
            media = MediaItem(
                url="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                title="Big Buck Bunny",
                description="Test video for WebOS casting",
                mime_type="video/mp4"
            )
            
            service.cast_media(device_id, media)
            
            # Keep connection alive
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\nDisconnecting...")
                service.disconnect_from_tv(device_id)
        else:
            print("Failed to connect to TV")
    else:
        print("No WebOS TVs found")
