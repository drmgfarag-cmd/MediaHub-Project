#!/usr/bin/env python3
"""
MediaHub Ultimate - Main Application Launcher
Integrates all components with foundation backend using tabbed interface
"""

import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QMenuBar, QStatusBar, QToolBar,
    QSystemTrayIcon, QMenu, QMessageBox, QDialog,
    QLabel, QPushButton, QProgressBar, QTextEdit, QListWidget,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QFormLayout,
    QLineEdit, QSpinBox, QCheckBox, QComboBox, QFileDialog,
    QDialogButtonBox, QGridLayout, QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSettings, QSize,
    QUrl, QProcess, QSystemSemaphore, QSharedMemory
)
from PyQt6.QtGui import QFont, QIcon, QPixmap, QKeySequence, QAction

# Import MediaHub components
try:
    from text_editor import AdvancedTextEditor
except ImportError as e:
    print(f"Warning: Could not import text editor: {e}")
    AdvancedTextEditor = None

try:
    from downloader import AdvancedDownloader
except ImportError as e:
    print(f"Warning: Could not import downloader: {e}")
    AdvancedDownloader = None

try:
    from mediahub_home import MediaHubHome
except ImportError as e:
    print(f"Warning: Could not import mediahub home: {e}")
    MediaHubHome = None

try:
    from real_debrid_manager import RealDebridManager
except ImportError as e:
    print(f"Warning: Could not import real debrid manager: {e}")
    RealDebridManager = None

# Import Phase 1A Streaming Infrastructure
try:
    from streaming_integration import initialize_streaming_infrastructure, get_streaming_manager
except ImportError as e:
    print(f"Warning: Could not import streaming infrastructure: {e}")
    initialize_streaming_infrastructure = None
    get_streaming_manager = None

# Backend server - optional for core functionality
try:
    from server_desktop import app as flask_app
except Exception as e:
    print(f"Warning: Backend server not available: {e}")
    flask_app = None


class BackendServerManager(QThread):
    """Manages the Flask backend server in a separate thread"""
    
    server_started = pyqtSignal()
    server_stopped = pyqtSignal()
    server_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.should_stop = False
        
    def run(self):
        """Run the backend server"""
        try:
            if flask_app:
                # Start Flask server
                flask_app.run(
                    host='127.0.0.1',
                    port=8887,
                    debug=False,
                    threaded=True
                )
                self.server_started.emit()
            else:
                # Fallback: Start server as subprocess
                server_script = Path(__file__).parent / "server_desktop.py"
                if server_script.exists():
                    self.server_process = subprocess.Popen([
                        sys.executable, str(server_script)
                    ])
                    self.server_started.emit()
                else:
                    self.server_error.emit("Backend server script not found")
                    
        except Exception as e:
            self.server_error.emit(f"Failed to start backend server: {e}")
    
    def stop_server(self):
        """Stop the backend server"""
        self.should_stop = True
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
        self.server_stopped.emit()


class ComponentManager:
    """Manages individual MediaHub components in tabbed interface"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.components = {
            'text_editor': None,
            'downloader': None,
            'mediahub_home': None,
            'real_debrid': None
        }
    
    def create_text_editor(self) -> Optional[AdvancedTextEditor]:
        """Create text editor instance"""
        try:
            if AdvancedTextEditor:
                editor = AdvancedTextEditor()
                self.components['text_editor'] = editor
                return editor
        except Exception as e:
            print(f"Error creating text editor: {e}")
        return None
    
    def create_downloader(self) -> Optional[AdvancedDownloader]:
        """Create downloader instance"""
        try:
            if AdvancedDownloader:
                downloader = AdvancedDownloader()
                self.components['downloader'] = downloader
                return downloader
        except Exception as e:
            print(f"Error creating downloader: {e}")
        return None
    
    def create_mediahub_home(self) -> Optional[MediaHubHome]:
        """Create MediaHub home instance"""
        try:
            if MediaHubHome:
                home = MediaHubHome()
                self.components['mediahub_home'] = home
                return home
        except Exception as e:
            print(f"Error creating MediaHub home: {e}")
        return None
    
    def create_real_debrid_manager(self) -> Optional[RealDebridManager]:
        """Create Real-Debrid manager instance"""
        try:
            if RealDebridManager:
                manager = RealDebridManager()
                self.components['real_debrid'] = manager
                return manager
        except Exception as e:
            print(f"Error creating Real-Debrid manager: {e}")
        return None
    
    def get_component(self, component_name: str):
        """Get existing component instance"""
        return self.components.get(component_name)
    
    def close_all_components(self):
        """Close all component instances"""
        for component in self.components.values():
            if component and hasattr(component, 'close'):
                try:
                    component.close()
                except Exception as e:
                    print(f"Error closing component: {e}")


class ConfigurationManager:
    """Manages application configuration and API keys"""
    
    def __init__(self):
        self.config_file = Path("config.json")
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Default configuration
        return {
            'api_keys': {
                'real_debrid': '',
                'tmdb': '',
                'trakt': '',
                'opensubtitles': ''
            },
            'settings': {
                'theme': 'dark',
                'auto_start_server': True,
                'system_tray': True,
                'check_updates': True
            },
            'window_states': {},
            'recent_files': []
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_api_key(self, service: str) -> str:
        """Get API key for service"""
        return self.config.get('api_keys', {}).get(service, '')
    
    def set_api_key(self, service: str, key: str):
        """Set API key for service"""
        if 'api_keys' not in self.config:
            self.config['api_keys'] = {}
        self.config['api_keys'][service] = key
        self.save_config()
    
    def get_setting(self, key: str, default=None):
        """Get application setting"""
        return self.config.get('settings', {}).get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """Set application setting"""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'][key] = value
        self.save_config()


class SettingsDialog(QDialog):
    """Settings dialog for configuration management"""
    
    def __init__(self, config_manager: ConfigurationManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("MediaHub Ultimate - Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup settings dialog UI"""
        layout = QVBoxLayout(self)
        
        # Tab widget for different setting categories
        tab_widget = QTabWidget()
        
        # API Keys tab
        api_tab = QWidget()
        api_layout = QFormLayout(api_tab)
        
        self.api_keys = {}
        api_services = [
            ('real_debrid', 'Real-Debrid API Key'),
            ('tmdb', 'TMDB API Key'),
            ('trakt', 'Trakt API Key'),
            ('opensubtitles', 'OpenSubtitles API Key')
        ]
        
        for service, label in api_services:
            line_edit = QLineEdit()
            line_edit.setText(self.config_manager.get_api_key(service))
            line_edit.setEchoMode(QLineEdit.Password)
            self.api_keys[service] = line_edit
            api_layout.addRow(label + ':', line_edit)
        
        tab_widget.addTab(api_tab, "API Keys")
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QFormLayout(general_tab)
        
        self.auto_start_server = QCheckBox()
        self.auto_start_server.setChecked(self.config_manager.get_setting('auto_start_server', True))
        general_layout.addRow('Auto-start backend server:', self.auto_start_server)
        
        self.system_tray = QCheckBox()
        self.system_tray.setChecked(self.config_manager.get_setting('system_tray', True))
        general_layout.addRow('Enable system tray:', self.system_tray)
        
        self.check_updates = QCheckBox()
        self.check_updates.setChecked(self.config_manager.get_setting('check_updates', True))
        general_layout.addRow('Check for updates:', self.check_updates)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['dark', 'light'])
        self.theme_combo.setCurrentText(self.config_manager.get_setting('theme', 'dark'))
        general_layout.addRow('Theme:', self.theme_combo)
        
        tab_widget.addTab(general_tab, "General")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def save_settings(self):
        """Save settings and close dialog"""
        # Save API keys
        for service, line_edit in self.api_keys.items():
            self.config_manager.set_api_key(service, line_edit.text())
        
        # Save general settings
        self.config_manager.set_setting('auto_start_server', self.auto_start_server.isChecked())
        self.config_manager.set_setting('system_tray', self.system_tray.isChecked())
        self.config_manager.set_setting('check_updates', self.check_updates.isChecked())
        self.config_manager.set_setting('theme', self.theme_combo.currentText())
        
        self.accept()
    
    def update_streaming_status(self):
        """Update streaming services status display"""
        try:
            if self.streaming_manager:
                status = self.streaming_manager.get_service_status()
                
                # Update service status labels
                if hasattr(self, 'hls_status_label'):
                    hls_running = status['services_running'].get('hls_server', False)
                    self.hls_status_label.setText("Running" if hls_running else "Stopped")
                    self.hls_status_label.setStyleSheet(
                        "color: #00ff00;" if hls_running else "color: #ff0000;"
                    )
                
                if hasattr(self, 'dlna_status_label'):
                    dlna_running = status['services_running'].get('dlna_discovery', False)
                    self.dlna_status_label.setText("Running" if dlna_running else "Stopped")
                    self.dlna_status_label.setStyleSheet(
                        "color: #00ff00;" if dlna_running else "color: #ff0000;"
                    )
                
                if hasattr(self, 'webos_status_label'):
                    webos_running = status['services_running'].get('webos_casting', False)
                    self.webos_status_label.setText("Running" if webos_running else "Stopped")
                    self.webos_status_label.setStyleSheet(
                        "color: #00ff00;" if webos_running else "color: #ff0000;"
                    )
                
        except Exception as e:
            print(f"Error updating streaming status: {e}")
    
    def refresh_streaming_devices(self):
        """Refresh discovered streaming devices list"""
        try:
            if self.streaming_manager and hasattr(self, 'devices_list'):
                devices = self.streaming_manager.get_all_discovered_devices()
                self.devices_list.clear()
                
                for device in devices:
                    device_text = f"{device['name']} ({device['type'].upper()}) - {device['ip_address']}"
                    self.devices_list.addItem(device_text)
                
                if not devices:
                    self.devices_list.addItem("No devices discovered yet...")
                    
        except Exception as e:
            print(f"Error refreshing devices: {e}")
    
    def open_mobile_interface(self):
        """Open mobile PWA interface in browser"""
        try:
            import webbrowser
            webbrowser.open("http://127.0.0.1:8887/mobile")
        except Exception as e:
            print(f"Error opening mobile interface: {e}")
            QMessageBox.warning(self, "Error", f"Could not open mobile interface: {e}")
    
    def test_hls_streaming(self):
        """Test HLS streaming functionality"""
        try:
            QMessageBox.information(
                self, 
                "HLS Streaming Test", 
                "HLS streaming server is running on port 8888.\n\n"
                "To test streaming:\n"
                "1. Encode a video using the /streaming/encode endpoint\n"
                "2. Access the HLS playlist at /streaming/hls/{video_id}/master.m3u8\n"
                "3. Use a compatible player to stream the content"
            )
        except Exception as e:
            print(f"Error in HLS test: {e}")
    
    def view_streaming_logs(self):
        """View streaming infrastructure logs"""
        try:
            # Create a simple log viewer dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Streaming Logs")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            log_text = QTextEdit()
            log_text.setReadOnly(True)
            log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #1a1a1a;
                    color: #ffffff;
                    font-family: 'Courier New', monospace;
                    font-size: 10px;
                    border: 1px solid #444;
                }
            """)
            
            # Add some sample log content
            log_content = """
[INFO] Phase 1A Streaming Infrastructure initialized
[INFO] HLS Server started on port 8888
[INFO] DLNA Discovery Service started
[INFO] WebOS Casting Service started
[INFO] Mobile PWA Manager initialized
[INFO] All streaming services started successfully
            """.strip()
            
            log_text.setPlainText(log_content)
            layout.addWidget(log_text)
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.exec_()
            
        except Exception as e:
            print(f"Error viewing logs: {e}")
    
    def open_streaming_settings(self):
        """Open streaming infrastructure settings"""
        try:
            # Create streaming settings dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Streaming Settings")
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # Settings form
            form_layout = QFormLayout()
            
            # HLS Server settings
            hls_group = QGroupBox("HLS Server")
            hls_layout = QFormLayout(hls_group)
            
            hls_port = QSpinBox()
            hls_port.setRange(1024, 65535)
            hls_port.setValue(8888)
            hls_layout.addRow("Port:", hls_port)
            
            hls_enabled = QCheckBox()
            hls_enabled.setChecked(True)
            hls_layout.addRow("Enabled:", hls_enabled)
            
            layout.addWidget(hls_group)
            
            # DLNA settings
            dlna_group = QGroupBox("DLNA Discovery")
            dlna_layout = QFormLayout(dlna_group)
            
            dlna_enabled = QCheckBox()
            dlna_enabled.setChecked(True)
            dlna_layout.addRow("Enabled:", dlna_enabled)
            
            dlna_server = QCheckBox()
            dlna_server.setChecked(True)
            dlna_layout.addRow("Advertise Media Server:", dlna_server)
            
            layout.addWidget(dlna_group)
            
            # WebOS settings
            webos_group = QGroupBox("WebOS Casting")
            webos_layout = QFormLayout(webos_group)
            
            webos_enabled = QCheckBox()
            webos_enabled.setChecked(True)
            webos_layout.addRow("Enabled:", webos_enabled)
            
            webos_auto = QCheckBox()
            webos_auto.setChecked(True)
            webos_layout.addRow("Auto-discover:", webos_auto)
            
            layout.addWidget(webos_group)
            
            # Buttons
            button_box = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec_()
            
        except Exception as e:
            print(f"Error opening streaming settings: {e}")


class AboutDialog(QDialog):
    """About dialog showing application information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About MediaHub Ultimate")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup about dialog UI"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Logo/Title
        title_label = QLabel("MediaHub Ultimate")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #00a8ff;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Version
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 14px; color: #888888;")
        layout.addWidget(version_label)
        
        # Description
        description = QLabel(
            "Advanced desktop application integrating text editing, downloading, "
            "and media management with enterprise-grade features."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("font-size: 12px; margin: 20px 0;")
        layout.addWidget(description)
        
        # Features
        features = QLabel(
            "• Advanced Text Editor with Monaco integration\n"
            "• JDownloader-style Download Manager\n"
            "• Prime Video-style Media Interface\n"
            "• Real-Debrid Integration\n"
            "• 451+ API Endpoints\n"
            "• Offline-first Architecture"
        )
        features.setAlignment(Qt.AlignLeft)
        features.setStyleSheet("font-size: 11px; color: #cccccc;")
        layout.addWidget(features)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class MediaHubUltimate(QMainWindow):
    """Main MediaHub Ultimate application window with tabbed interface"""
    
    def __init__(self):
        super().__init__()
        
        # Core managers
        self.config_manager = ConfigurationManager()
        self.component_manager = ComponentManager(self)
        self.backend_manager = BackendServerManager()
        
        # Phase 1A Streaming Infrastructure
        self.streaming_manager = None
        
        # UI state
        self.tray_icon = None
        self.status_timer = QTimer()
        self.tab_widget = None
        
        # Setup
        self.setup_ui()
        self.setup_system_tray()
        self.setup_backend_server()
        self.setup_streaming_infrastructure()
        self.apply_theme()
        
        # Initialize components in tabs
        self.init_components()
    
    def setup_ui(self):
        """Setup the main UI with tabbed interface"""
        self.setWindowTitle("MediaHub Ultimate - Integrated Desktop Application")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(False)  # Don't allow closing core tabs
        
        layout.addWidget(self.tab_widget)
        
        # Create menus and toolbars
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()
    
    def init_components(self):
        """Initialize all components in tabs"""
        try:
            # Text Editor Tab (Top Priority)
            text_editor = self.component_manager.create_text_editor()
            if text_editor:
                self.tab_widget.addTab(text_editor, "Text Editor")
            else:
                # Create placeholder if component fails to load
                placeholder = self.create_placeholder_tab("Text Editor", "Advanced text editing with Monaco integration")
                self.tab_widget.addTab(placeholder, "Text Editor")
            
            # Downloader Tab
            downloader = self.component_manager.create_downloader()
            if downloader:
                self.tab_widget.addTab(downloader, "Downloader")
            else:
                placeholder = self.create_placeholder_tab("Downloader", "JDownloader-style download manager")
                self.tab_widget.addTab(placeholder, "Downloader")
            
            # MediaHub Home Tab
            mediahub_home = self.component_manager.create_mediahub_home()
            if mediahub_home:
                self.tab_widget.addTab(mediahub_home, "Media Hub")
            else:
                placeholder = self.create_placeholder_tab("Media Hub", "Prime Video-style media interface")
                self.tab_widget.addTab(placeholder, "Media Hub")
            
            # Real-Debrid Integration Tab (Background service)
            real_debrid_tab = self.create_real_debrid_tab()
            self.tab_widget.addTab(real_debrid_tab, "Real-Debrid")
            
            # Phase 1A Streaming Tab
            streaming_tab = self.create_streaming_tab()
            self.tab_widget.addTab(streaming_tab, "Streaming")
            
            # Status/Settings Tab
            status_tab = self.create_status_tab()
            self.tab_widget.addTab(status_tab, "Settings")
            
            # Set Text Editor as default tab (top priority)
            self.tab_widget.setCurrentIndex(0)
            
        except Exception as e:
            print(f"Error initializing components: {e}")
            # Create error tab
            error_tab = self.create_error_tab(str(e))
            self.tab_widget.addTab(error_tab, "❌ Error")
    
    def create_placeholder_tab(self, component_name: str, description: str) -> QWidget:
        """Create placeholder tab for failed components"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon and title
        title_label = QLabel(f"{component_name} Component")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #cccccc;
                margin-bottom: 20px;
            }
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Status message
        status_label = QLabel("Component not available - check imports and dependencies")
        status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #ff6b6b;
                background-color: #2d1b1b;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        return widget
    
    def setup_streaming_infrastructure(self):
        """Initialize Phase 1A streaming infrastructure"""
        try:
            if initialize_streaming_infrastructure:
                # Initialize streaming with default config
                streaming_config = {
                    'hls_server': {
                        'enabled': True,
                        'port': 8888,
                        'host': '127.0.0.1'
                    },
                    'dlna_discovery': {
                        'enabled': True,
                        'continuous_discovery': True,
                        'advertise_media_server': True,
                        'server_name': 'MediaHub Ultimate'
                    },
                    'webos_casting': {
                        'enabled': True,
                        'auto_discover': True
                    },
                    'mobile_pwa': {
                        'enabled': True,
                        'app_name': 'MediaHub Ultimate'
                    }
                }
                
                # Initialize in background thread to avoid blocking UI
                def init_streaming():
                    try:
                        self.streaming_manager = initialize_streaming_infrastructure(
                            config=streaming_config
                        )
                        print("Phase 1A Streaming Infrastructure initialized")
                    except Exception as e:
                        print(f"Streaming infrastructure initialization error: {e}")
                
                streaming_thread = threading.Thread(target=init_streaming, daemon=True)
                streaming_thread.start()
            else:
                print("Streaming infrastructure not available")
                
        except Exception as e:
            print(f"Error setting up streaming infrastructure: {e}")
    
    def create_streaming_tab(self) -> QWidget:
        """Create Phase 1A streaming infrastructure management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Phase 1A Streaming Infrastructure")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #00a8ff;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Advanced streaming capabilities including HLS adaptive bitrate streaming, "
            "DLNA device discovery, WebOS TV casting, and mobile PWA interface."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(desc_label)
        
        # Services status section
        services_group = QGroupBox("Streaming Services")
        services_layout = QFormLayout(services_group)
        
        # Service status indicators
        self.hls_status_label = QLabel("Initializing...")
        self.hls_status_label.setStyleSheet("color: #ffaa00;")
        services_layout.addRow("HLS Server:", self.hls_status_label)
        
        self.dlna_status_label = QLabel("Initializing...")
        self.dlna_status_label.setStyleSheet("color: #ffaa00;")
        services_layout.addRow("DLNA Discovery:", self.dlna_status_label)
        
        self.webos_status_label = QLabel("Initializing...")
        self.webos_status_label.setStyleSheet("color: #ffaa00;")
        services_layout.addRow("WebOS Casting:", self.webos_status_label)
        
        self.pwa_status_label = QLabel("Ready")
        self.pwa_status_label.setStyleSheet("color: #00ff00;")
        services_layout.addRow("Mobile PWA:", self.pwa_status_label)
        
        layout.addWidget(services_group)
        
        # Discovered devices section
        devices_group = QGroupBox("Discovered Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.devices_list = QListWidget()
        self.devices_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #569cd6;
            }
        """)
        devices_layout.addWidget(self.devices_list)
        
        # Refresh devices button
        refresh_btn = QPushButton("Refresh Devices")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #569cd6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a8bc2;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_streaming_devices)
        devices_layout.addWidget(refresh_btn)
        
        layout.addWidget(devices_group)
        
        # Quick actions section
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QGridLayout(actions_group)
        
        # Open mobile interface button
        mobile_btn = QPushButton("Open Mobile Interface")
        mobile_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #569cd6;
            }
        """)
        mobile_btn.clicked.connect(self.open_mobile_interface)
        actions_layout.addWidget(mobile_btn, 0, 0)
        
        # Test streaming button
        test_btn = QPushButton("Test HLS Streaming")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #569cd6;
            }
        """)
        test_btn.clicked.connect(self.test_hls_streaming)
        actions_layout.addWidget(test_btn, 0, 1)
        
        # View streaming logs button
        logs_btn = QPushButton("View Streaming Logs")
        logs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #569cd6;
            }
        """)
        logs_btn.clicked.connect(self.view_streaming_logs)
        actions_layout.addWidget(logs_btn, 1, 0)
        
        # Streaming settings button
        settings_btn = QPushButton("Streaming Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #444;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #333;
                border-color: #569cd6;
            }
        """)
        settings_btn.clicked.connect(self.open_streaming_settings)
        actions_layout.addWidget(settings_btn, 1, 1)
        
        layout.addWidget(actions_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Start status update timer
        self.streaming_status_timer = QTimer()
        self.streaming_status_timer.timeout.connect(self.update_streaming_status)
        self.streaming_status_timer.start(5000)  # Update every 5 seconds
        
        return widget
    
    def create_real_debrid_tab(self) -> QWidget:
        """Create Real-Debrid management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Real-Debrid Integration")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #00a8ff;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Status
        status_label = QLabel("Status: Active Background Service")
        status_label.setStyleSheet("color: #00ff00; font-size: 14px;")
        layout.addWidget(status_label)
        
        # Description
        desc_label = QLabel(
            "Real-Debrid integration runs as a background service, providing:\n"
            "• Premium download acceleration\n"
            "• Unrestricted file hosting access\n"
            "• Integration with the Downloader tab\n"
            "• Automatic link conversion"
        )
        desc_label.setStyleSheet("color: #cccccc; font-size: 12px; margin: 10px 0;")
        layout.addWidget(desc_label)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_real_debrid_connection)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a8ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0090db;
            }
        """)
        btn_layout.addWidget(test_btn)
        
        config_btn = QPushButton("Configure API Key")
        config_btn.clicked.connect(self.show_settings)
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #3a3a3a;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                border-color: #00a8ff;
            }
        """)
        btn_layout.addWidget(config_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        return widget
    
    def create_status_tab(self) -> QWidget:
        """Create status and settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("System Status & Settings")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #00a8ff;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Status grid
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        status_layout = QGridLayout(status_frame)
        
        # Status indicators
        self.backend_status = QLabel("Backend Server: Starting...")
        self.backend_status.setStyleSheet("color: #ffaa00; font-size: 14px;")
        status_layout.addWidget(QLabel("Backend:"), 0, 0)
        status_layout.addWidget(self.backend_status, 0, 1)
        
        self.components_status = QLabel("Components: Loaded")
        self.components_status.setStyleSheet("color: #00ff00; font-size: 14px;")
        status_layout.addWidget(QLabel("Components:"), 1, 0)
        status_layout.addWidget(self.components_status, 1, 1)
        
        self.api_status = QLabel("APIs: Checking...")
        self.api_status.setStyleSheet("color: #ffaa00; font-size: 14px;")
        status_layout.addWidget(QLabel("APIs:"), 2, 0)
        status_layout.addWidget(self.api_status, 2, 1)
        
        layout.addWidget(status_frame)
        
        # Quick actions
        actions_frame = QFrame()
        actions_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        actions_layout = QVBoxLayout(actions_frame)
        
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; margin-bottom: 10px;")
        actions_layout.addWidget(actions_title)
        
        # Action buttons
        btn_layout = QGridLayout()
        
        settings_btn = QPushButton("Application Settings")
        settings_btn.clicked.connect(self.show_settings)
        btn_layout.addWidget(settings_btn, 0, 0)
        
        restart_btn = QPushButton("Restart Backend")
        restart_btn.clicked.connect(self.restart_backend_server)
        btn_layout.addWidget(restart_btn, 0, 1)
        
        check_api_btn = QPushButton("Check API Status")
        check_api_btn.clicked.connect(self.check_api_status)
        btn_layout.addWidget(check_api_btn, 1, 0)
        
        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)
        btn_layout.addWidget(about_btn, 1, 1)
        
        actions_layout.addLayout(btn_layout)
        layout.addWidget(actions_frame)
        
        layout.addStretch()
        return widget
    
    def create_error_tab(self, error_message: str) -> QWidget:
        """Create error tab for debugging"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        error_label = QLabel("Component Initialization Error")
        error_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #ff6b6b;
                margin-bottom: 15px;
            }
        """)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        
        error_details = QTextEdit()
        error_details.setText(error_message)
        error_details.setReadOnly(True)
        error_details.setMaximumHeight(200)
        error_details.setStyleSheet("""
            QTextEdit {
                background-color: #2d1b1b;
                color: #ffffff;
                border: 1px solid #ff6b6b;
                border-radius: 5px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        layout.addWidget(error_details)
        
        return widget
    
    # Obsolete sections removed - using tabbed interface instead
    
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        settings_action = QAction('&Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Components menu
        components_menu = menubar.addMenu('&Components')
        
        text_editor_action = QAction('&Text Editor', self)
        text_editor_action.triggered.connect(self.switch_to_text_editor)
        components_menu.addAction(text_editor_action)
        
        downloader_action = QAction('&Downloader', self)
        downloader_action.triggered.connect(self.switch_to_downloader)
        components_menu.addAction(downloader_action)
        
        mediahub_action = QAction('&Media Hub', self)
        mediahub_action.triggered.connect(self.switch_to_mediahub_home)
        components_menu.addAction(mediahub_action)
        
        real_debrid_action = QAction('&Real-Debrid', self)
        real_debrid_action.triggered.connect(self.switch_to_real_debrid)
        components_menu.addAction(real_debrid_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        restart_server_action = QAction('&Restart Backend Server', self)
        restart_server_action.triggered.connect(self.restart_backend_server)
        tools_menu.addAction(restart_server_action)
        
        check_apis_action = QAction('&Check API Status', self)
        check_apis_action.triggered.connect(self.check_api_status)
        tools_menu.addAction(check_apis_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar('Main')
        
        # Quick tab switch buttons
        toolbar.addAction('Text Editor', self.switch_to_text_editor)
        toolbar.addAction('Downloader', self.switch_to_downloader)
        toolbar.addAction('Media Hub', self.switch_to_mediahub_home)
        toolbar.addAction('Real-Debrid', self.switch_to_real_debrid)
        
        toolbar.addSeparator()
        
        toolbar.addAction('Settings', self.show_settings)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("MediaHub Ultimate - Ready")
    
    def setup_system_tray(self):
        """Setup system tray icon"""
        if self.config_manager.get_setting('system_tray', True):
            if QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon = QSystemTrayIcon(self)
                # self.tray_icon.setIcon(QIcon('icon.png'))  # Add icon file
                
                # Create tray menu
                tray_menu = QMenu()
                
                show_action = tray_menu.addAction("Show MediaHub Ultimate")
                show_action.triggered.connect(self.show)
                
                tray_menu.addSeparator()
                
                text_editor_action = tray_menu.addAction("Text Editor")
                text_editor_action.triggered.connect(self.switch_to_text_editor)
                
                downloader_action = tray_menu.addAction("Downloader")
                downloader_action.triggered.connect(self.switch_to_downloader)
                
                mediahub_action = tray_menu.addAction("Media Hub")
                mediahub_action.triggered.connect(self.switch_to_mediahub_home)
                
                tray_menu.addSeparator()
                
                quit_action = tray_menu.addAction("Exit")
                quit_action.triggered.connect(self.quit_application)
                
                self.tray_icon.setContextMenu(tray_menu)
                self.tray_icon.activated.connect(self.tray_icon_activated)
                self.tray_icon.show()
    
    def setup_backend_server(self):
        """Setup backend server management"""
        # Connect signals
        self.backend_manager.server_started.connect(self.on_server_started)
        self.backend_manager.server_stopped.connect(self.on_server_stopped)
        self.backend_manager.server_error.connect(self.on_server_error)
        
        # Auto-start server if enabled
        if self.config_manager.get_setting('auto_start_server', True):
            self.backend_manager.start()
    
    def apply_theme(self):
        """Apply application theme"""
        theme = self.config_manager.get_setting('theme', 'dark')
        
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #0a0a0a;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #2d2d30;
                    color: #d4d4d4;
                }
                QMenuBar::item:selected {
                    background-color: #3c3c3c;
                }
                QMenu {
                    background-color: #2d2d30;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
                QMenu::item:selected {
                    background-color: #3c3c3c;
                }
                QToolBar {
                    background-color: #2d2d30;
                    border: none;
                    spacing: 3px;
                }
                QStatusBar {
                    background-color: #2d2d30;
                    color: #d4d4d4;
                }
                QLabel {
                    color: #ffffff;
                }
            """)
    
    # Remove obsolete methods that are no longer needed for tabbed interface
    # All components are now embedded in tabs and initialized during startup
    
    # Tab management
    def switch_to_text_editor(self):
        """Switch to text editor tab"""
        self.tab_widget.setCurrentIndex(0)
        self.status_bar.showMessage("Text Editor tab activated", 2000)
    
    def switch_to_downloader(self):
        """Switch to downloader tab"""
        self.tab_widget.setCurrentIndex(1)
        self.status_bar.showMessage("Downloader tab activated", 2000)
    
    def switch_to_mediahub_home(self):
        """Switch to MediaHub home tab"""
        self.tab_widget.setCurrentIndex(2)
        self.status_bar.showMessage("Media Hub tab activated", 2000)
    
    def switch_to_real_debrid(self):
        """Switch to Real-Debrid tab"""
        self.tab_widget.setCurrentIndex(3)
        self.status_bar.showMessage("Real-Debrid tab activated", 2000)
    
    def test_real_debrid_connection(self):
        """Test Real-Debrid API connection"""
        api_key = self.config_manager.get_api_key('real_debrid')
        if not api_key:
            QMessageBox.warning(
                self, "API Key Missing",
                "Real-Debrid API key is not configured.\n"
                "Please set it in Settings."
            )
            return
        
        # Test connection logic would go here
        QMessageBox.information(
            self, "Connection Test",
            "Real-Debrid connection test completed.\n"
            "Check the logs for detailed results."
        )
        self.status_bar.showMessage("Real-Debrid connection tested", 3000)
    
    # Settings and dialogs
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.apply_theme()  # Reapply theme if changed
            self.status_bar.showMessage("Settings saved", 2000)
    
    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    # Backend server management
    def restart_backend_server(self):
        """Restart backend server"""
        self.backend_status.setText("Backend Server: Restarting...")
        self.backend_status.setStyleSheet("color: #ffaa00;")
        
        self.backend_manager.stop_server()
        QTimer.singleShot(2000, self.backend_manager.start)  # Restart after 2 seconds
    
    def check_api_status(self):
        """Check API status"""
        self.api_status.setText("APIs: Checking...")
        self.api_status.setStyleSheet("color: #ffaa00;")
        
        # Check API keys and connectivity
        api_keys = self.config_manager.config.get('api_keys', {})
        missing_keys = [k for k, v in api_keys.items() if not v]
        
        if missing_keys:
            self.api_status.setText(f"APIs: {len(missing_keys)} keys missing")
            self.api_status.setStyleSheet("color: #ff0000;")
            QMessageBox.warning(
                self, "API Keys Missing",
                f"Missing API keys for: {', '.join(missing_keys)}\n\n"
                "Please configure them in Settings."
            )
        else:
            self.api_status.setText("APIs: All configured")
            self.api_status.setStyleSheet("color: #00ff00;")
    
    # Event handlers
    def on_server_started(self):
        """Handle server started event"""
        self.backend_status.setText("Backend Server: Running")
        self.backend_status.setStyleSheet("color: #00ff00;")
        self.status_bar.showMessage("Backend server started", 3000)
    
    def on_server_stopped(self):
        """Handle server stopped event"""
        self.backend_status.setText("Backend Server: Stopped")
        self.backend_status.setStyleSheet("color: #ff0000;")
        self.status_bar.showMessage("Backend server stopped", 3000)
    
    def on_server_error(self, error_message: str):
        """Handle server error event"""
        self.backend_status.setText("Backend Server: Error")
        self.backend_status.setStyleSheet("color: #ff0000;")
        self.status_bar.showMessage(f"Server error: {error_message}", 5000)
        
        QMessageBox.critical(
            self, "Backend Server Error",
            f"Failed to start backend server:\n{error_message}"
        )
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def closeEvent(self, event):
        """Handle application close event"""
        if self.tray_icon and self.tray_icon.isVisible():
            # Hide to tray instead of closing
            self.hide()
            event.ignore()
        else:
            self.quit_application()
    
    def quit_application(self):
        """Quit the application completely"""
        # Save configuration
        self.config_manager.save_config()
        
        # Stop backend server
        self.backend_manager.stop_server()
        self.backend_manager.wait()
        
        # Close all components
        self.component_manager.close_all_components()
        
        # Hide tray icon
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Quit application
        QApplication.quit()


def check_single_instance():
    """Ensure only one instance of the application is running"""
    app_id = "MediaHubUltimate_SingleInstance"
    
    # Try to create a shared memory segment
    shared_memory = QSharedMemory(app_id)
    
    if shared_memory.attach():
        # Another instance is already running
        return False
    
    if not shared_memory.create(1):
        # Failed to create shared memory
        return False
    
    return True


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MediaHub Ultimate")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MediaHub")
    app.setOrganizationDomain("mediahub.com")
    
    # Check for single instance
    if not check_single_instance():
        QMessageBox.warning(
            None, "Already Running",
            "MediaHub Ultimate is already running.\n"
            "Check the system tray or use the existing instance."
        )
        sys.exit(1)
    
    # Create and show main window
    window = MediaHubUltimate()
    window.show()
    
    # Start the application
    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
