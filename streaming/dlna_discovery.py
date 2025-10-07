#!/usr/bin/env python3
"""
DLNA Discovery Service
Phase 1A Streaming Infrastructure Component

Provides device detection for DLNA-compatible devices with network scanning,
device enumeration, media server capabilities advertisement,
and cross-platform device communication.
"""

import socket
import threading
import time
import json
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
import requests
from dataclasses import dataclass


@dataclass
class DLNADevice:
    """Represents a discovered DLNA device"""
    uuid: str
    name: str
    manufacturer: str
    model: str
    device_type: str
    location: str
    ip_address: str
    port: int
    services: List[str]
    capabilities: List[str]
    discovered_at: datetime
    last_seen: datetime
    
    def to_dict(self) -> dict:
        return {
            'uuid': self.uuid,
            'name': self.name,
            'manufacturer': self.manufacturer,
            'model': self.model,
            'device_type': self.device_type,
            'location': self.location,
            'ip_address': self.ip_address,
            'port': self.port,
            'services': self.services,
            'capabilities': self.capabilities,
            'discovered_at': self.discovered_at.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }


class DLNADiscoveryService:
    """DLNA/UPnP discovery service for network device detection"""
    
    SSDP_ADDR = '239.255.255.250'
    SSDP_PORT = 1900
    
    # Common DLNA device types to search for
    SEARCH_TARGETS = [
        'upnp:rootdevice',
        'urn:schemas-upnp-org:device:MediaRenderer:1',
        'urn:schemas-upnp-org:device:MediaServer:1',
        'urn:schemas-upnp-org:service:AVTransport:1',
        'urn:schemas-upnp-org:service:RenderingControl:1'
    ]
    
    def __init__(self, interface_ip: str = None):
        self.interface_ip = interface_ip or self._get_local_ip()
        self.discovered_devices: Dict[str, DLNADevice] = {}
        self.discovery_active = False
        self.server_active = False
        self.discovery_thread = None
        self.server_thread = None
        self.callbacks: List[Callable] = []
        self.server_uuid = str(uuid.uuid4())
        
    def _get_local_ip(self) -> str:
        """Get the local IP address"""
        try:
            # Connect to a remote server to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"
    
    def add_device_callback(self, callback: Callable[[DLNADevice], None]):
        """Add callback for device discovery events"""
        self.callbacks.append(callback)
    
    def _notify_callbacks(self, device: DLNADevice):
        """Notify all callbacks of device discovery"""
        for callback in self.callbacks:
            try:
                callback(device)
            except Exception as e:
                print(f"Callback error: {e}")
    
    def start_discovery(self, continuous: bool = True):
        """Start DLNA device discovery"""
        if self.discovery_active:
            print("Discovery already active")
            return
        
        self.discovery_active = True
        self.discovery_thread = threading.Thread(
            target=self._discovery_worker,
            args=(continuous,),
            daemon=True
        )
        self.discovery_thread.start()
        print("DLNA discovery started")
    
    def stop_discovery(self):
        """Stop DLNA device discovery"""
        self.discovery_active = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=5)
        print("DLNA discovery stopped")
    
    def start_media_server(self, media_root: str, server_name: str = "MediaHub"):
        """Start advertising as DLNA media server"""
        if self.server_active:
            print("Media server already active")
            return
        
        self.server_active = True
        self.media_root = media_root
        self.server_name = server_name
        
        self.server_thread = threading.Thread(
            target=self._server_worker,
            daemon=True
        )
        self.server_thread.start()
        print(f"DLNA media server '{server_name}' started")
    
    def stop_media_server(self):
        """Stop DLNA media server advertisement"""
        self.server_active = False
        if self.server_thread:
            self.server_thread.join(timeout=5)
        print("DLNA media server stopped")
    
    def _discovery_worker(self, continuous: bool):
        """Worker thread for device discovery"""
        while self.discovery_active:
            try:
                self._send_ssdp_discovery()
                
                if not continuous:
                    break
                    
                # Wait before next discovery cycle
                time.sleep(30)
                
            except Exception as e:
                print(f"Discovery worker error: {e}")
                time.sleep(5)
    
    def _send_ssdp_discovery(self):
        """Send SSDP M-SEARCH messages"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        try:
            for target in self.SEARCH_TARGETS:
                message = (
                    "M-SEARCH * HTTP/1.1\r\n"
                    f"HOST: {self.SSDP_ADDR}:{self.SSDP_PORT}\r\n"
                    "MAN: \"ssdp:discover\"\r\n"
                    "ST: {}\r\n"
                    "MX: 3\r\n\r\n"
                ).format(target)
                
                sock.sendto(message.encode(), (self.SSDP_ADDR, self.SSDP_PORT))
            
            # Listen for responses
            self._listen_for_responses(sock)
            
        except Exception as e:
            print(f"SSDP discovery error: {e}")
        finally:
            sock.close()
    
    def _listen_for_responses(self, sock: socket.socket, timeout: int = 10):
        """Listen for SSDP discovery responses"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(4096)
                response = data.decode('utf-8')
                
                if 'HTTP/1.1 200 OK' in response:
                    self._parse_ssdp_response(response, addr[0])
                    
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Response listening error: {e}")
                break
    
    def _parse_ssdp_response(self, response: str, ip_address: str):
        """Parse SSDP response and extract device information"""
        try:
            lines = response.split('\r\n')
            location = None
            usn = None
            
            for line in lines:
                if line.upper().startswith('LOCATION:'):
                    location = line.split(':', 1)[1].strip()
                elif line.upper().startswith('USN:'):
                    usn = line.split(':', 1)[1].strip()
            
            if location and usn:
                device_uuid = self._extract_uuid_from_usn(usn)
                if device_uuid and device_uuid not in self.discovered_devices:
                    # Fetch device description
                    device = self._fetch_device_description(location, ip_address, device_uuid)
                    if device:
                        self.discovered_devices[device_uuid] = device
                        self._notify_callbacks(device)
                        print(f"Discovered DLNA device: {device.name} ({device.ip_address})")
                
        except Exception as e:
            print(f"Response parsing error: {e}")
    
    def _extract_uuid_from_usn(self, usn: str) -> Optional[str]:
        """Extract UUID from USN string"""
        try:
            if 'uuid:' in usn:
                parts = usn.split('uuid:')[1].split('::')
                return parts[0] if parts else None
        except Exception:
            pass
        return None
    
    def _fetch_device_description(self, location: str, ip_address: str, device_uuid: str) -> Optional[DLNADevice]:
        """Fetch and parse device description XML"""
        try:
            response = requests.get(location, timeout=10)
            if response.status_code == 200:
                return self._parse_device_description(response.text, location, ip_address, device_uuid)
        except Exception as e:
            print(f"Error fetching device description: {e}")
        return None
    
    def _parse_device_description(self, xml_content: str, location: str, ip_address: str, device_uuid: str) -> Optional[DLNADevice]:
        """Parse device description XML"""
        try:
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            ns = {'upnp': 'urn:schemas-upnp-org:device-1-0'}
            
            device_elem = root.find('.//upnp:device', ns)
            if device_elem is None:
                return None
            
            # Extract device information
            name = self._get_xml_text(device_elem, 'upnp:friendlyName', ns) or 'Unknown Device'
            manufacturer = self._get_xml_text(device_elem, 'upnp:manufacturer', ns) or 'Unknown'
            model = self._get_xml_text(device_elem, 'upnp:modelName', ns) or 'Unknown'
            device_type = self._get_xml_text(device_elem, 'upnp:deviceType', ns) or 'Unknown'
            
            # Extract services
            services = []
            service_list = device_elem.find('upnp:serviceList', ns)
            if service_list is not None:
                for service in service_list.findall('upnp:service', ns):
                    service_type = self._get_xml_text(service, 'upnp:serviceType', ns)
                    if service_type:
                        services.append(service_type)
            
            # Determine capabilities based on services
            capabilities = self._determine_capabilities(services)
            
            # Extract port from location
            parsed_url = urlparse(location)
            port = parsed_url.port or 80
            
            now = datetime.now()
            
            return DLNADevice(
                uuid=device_uuid,
                name=name,
                manufacturer=manufacturer,
                model=model,
                device_type=device_type,
                location=location,
                ip_address=ip_address,
                port=port,
                services=services,
                capabilities=capabilities,
                discovered_at=now,
                last_seen=now
            )
            
        except Exception as e:
            print(f"XML parsing error: {e}")
            return None
    
    def _get_xml_text(self, parent, tag: str, namespaces: dict) -> Optional[str]:
        """Safely extract text from XML element"""
        element = parent.find(tag, namespaces)
        return element.text if element is not None else None
    
    def _determine_capabilities(self, services: List[str]) -> List[str]:
        """Determine device capabilities from services"""
        capabilities = []
        
        service_map = {
            'AVTransport': 'media_playback',
            'RenderingControl': 'volume_control',
            'ContentDirectory': 'media_server',
            'ConnectionManager': 'connection_management'
        }
        
        for service in services:
            for key, capability in service_map.items():
                if key in service and capability not in capabilities:
                    capabilities.append(capability)
        
        return capabilities
    
    def _server_worker(self):
        """Worker thread for DLNA media server advertisement"""
        while self.server_active:
            try:
                self._send_ssdp_notification()
                time.sleep(60)  # Send notification every minute
                
            except Exception as e:
                print(f"Server worker error: {e}")
                time.sleep(10)
    
    def _send_ssdp_notification(self):
        """Send SSDP NOTIFY messages to advertise media server"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            # NOTIFY message for media server
            message = (
                "NOTIFY * HTTP/1.1\r\n"
                f"HOST: {self.SSDP_ADDR}:{self.SSDP_PORT}\r\n"
                "CACHE-CONTROL: max-age=120\r\n"
                f"LOCATION: http://{self.interface_ip}:8080/device_description.xml\r\n"
                "NT: urn:schemas-upnp-org:device:MediaServer:1\r\n"
                "NTS: ssdp:alive\r\n"
                f"USN: uuid:{self.server_uuid}::urn:schemas-upnp-org:device:MediaServer:1\r\n"
                "SERVER: MediaHub/1.0 UPnP/1.0 DLNA/1.5\r\n\r\n"
            )
            
            sock.sendto(message.encode(), (self.SSDP_ADDR, self.SSDP_PORT))
            
        except Exception as e:
            print(f"SSDP notification error: {e}")
        finally:
            sock.close()
    
    def get_discovered_devices(self) -> List[Dict]:
        """Get all discovered devices"""
        # Clean up old devices (not seen for 5+ minutes)
        cutoff = datetime.now() - timedelta(minutes=5)
        active_devices = {
            uuid: device for uuid, device in self.discovered_devices.items()
            if device.last_seen > cutoff
        }
        self.discovered_devices = active_devices
        
        return [device.to_dict() for device in active_devices.values()]
    
    def get_device_by_uuid(self, device_uuid: str) -> Optional[DLNADevice]:
        """Get specific device by UUID"""
        return self.discovered_devices.get(device_uuid)
    
    def refresh_device(self, device_uuid: str) -> bool:
        """Refresh device information"""
        device = self.discovered_devices.get(device_uuid)
        if device:
            try:
                # Re-fetch device description
                updated_device = self._fetch_device_description(
                    device.location, device.ip_address, device_uuid
                )
                if updated_device:
                    # Preserve discovery time but update last_seen
                    updated_device.discovered_at = device.discovered_at
                    self.discovered_devices[device_uuid] = updated_device
                    return True
            except Exception as e:
                print(f"Device refresh error: {e}")
        return False
    
    def get_media_renderers(self) -> List[Dict]:
        """Get devices capable of media rendering"""
        renderers = []
        for device in self.discovered_devices.values():
            if 'media_playback' in device.capabilities:
                renderers.append(device.to_dict())
        return renderers
    
    def get_media_servers(self) -> List[Dict]:
        """Get devices acting as media servers"""
        servers = []
        for device in self.discovered_devices.values():
            if 'media_server' in device.capabilities:
                servers.append(device.to_dict())
        return servers


# Standalone service for testing
if __name__ == '__main__':
    def on_device_discovered(device: DLNADevice):
        print(f"Device discovered: {device.name} at {device.ip_address}")
        print(f"  Capabilities: {', '.join(device.capabilities)}")
    
    service = DLNADiscoveryService()
    service.add_device_callback(on_device_discovered)
    
    service.start_discovery()
    service.start_media_server("/path/to/media", "MediaHub Test Server")
    
    try:
        while True:
            time.sleep(10)
            devices = service.get_discovered_devices()
            print(f"\nCurrently {len(devices)} devices discovered")
    except KeyboardInterrupt:
        print("\nShutting down...")
        service.stop_discovery()
        service.stop_media_server()
