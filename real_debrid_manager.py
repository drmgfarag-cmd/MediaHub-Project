#!/usr/bin/env python3
"""
Real-Debrid Manager - GUI Interface for MediaHub Ultimate
Implements batch upload/download with smart file selection and automation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import time
import requests
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
import mimetypes

class RealDebridManager:
    """Real-Debrid Manager with GUI automation and batch processing"""
    
    def __init__(self, master=None):
        self.master = master or tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.setup_gui()
        self.setup_logging_queue()
        
        # Backend server integration
        self.server_url = "http://localhost:8887"  # Desktop server URL
        self.api_key = ""
        self.max_workers = 4  # Concurrent workers as specified
        
        # Import requests for API calls
        try:
            import requests
            self.requests_available = True
        except ImportError:
            self.requests_available = False
            self.log_message("Warning: requests library not available for API calls")
        
        # File processing settings
        self.smart_selection_rules = {
            'skip_samples': True,
            'prefer_media_types': ['.mp4', '.mkv', '.avi', '.mov', '.m4v', '.wmv'],
            'include_subtitles': ['.srt', '.sub', '.idx', '.ass', '.vtt'],
            'include_archives': ['.rar', '.zip', '.7z'],
            'min_file_size_mb': 50  # Skip files smaller than 50MB (likely samples)
        }
        
        # Setup backend integration on startup
        self.master.after(1000, self.setup_backend_integration)  # Delay to allow GUI to load
        
    def setup_window(self):
        """Configure the main window"""
        self.master.title("Real-Debrid Manager - MediaHub Ultimate")
        self.master.geometry("900x700")
        self.master.configure(bg='#1a1a1a')  # Dark theme
        
        # Configure style for dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Dark theme colors
        self.style.configure('Dark.TFrame', background='#1a1a1a')
        self.style.configure('Dark.TLabel', background='#1a1a1a', foreground='#ffffff')
        self.style.configure('Dark.TButton', background='#333333', foreground='#ffffff')
        self.style.configure('Dark.TCheckbutton', background='#1a1a1a', foreground='#ffffff')
        
    def setup_variables(self):
        """Initialize tkinter variables"""
        self.input_folder_var = tk.StringVar(value="Select Input Folder...")
        self.output_folder_var = tk.StringVar(value="Select Output Folder...")
        self.auto_download_var = tk.BooleanVar(value=True)
        self.processing_var = tk.BooleanVar(value=False)
        self.progress_var = tk.DoubleVar(value=0.0)
        
    def setup_gui(self):
        """Create the GUI elements"""
        # Main container
        main_frame = ttk.Frame(self.master, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Real-Debrid Manager", 
                               font=('Arial', 16, 'bold'), style='Dark.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Folder selection frame
        folder_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Input folder selection
        input_frame = ttk.Frame(folder_frame, style='Dark.TFrame')
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Input Folder:", style='Dark.TLabel').pack(anchor=tk.W)
        input_button_frame = ttk.Frame(input_frame, style='Dark.TFrame')
        input_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.input_folder_button = ttk.Button(input_button_frame, 
                                             textvariable=self.input_folder_var,
                                             command=self.browse_input_folder,
                                             style='Dark.TButton')
        self.input_folder_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Output folder selection
        output_frame = ttk.Frame(folder_frame, style='Dark.TFrame')
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Output Folder:", style='Dark.TLabel').pack(anchor=tk.W)
        output_button_frame = ttk.Frame(output_frame, style='Dark.TFrame')
        output_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.output_folder_button = ttk.Button(output_button_frame,
                                              textvariable=self.output_folder_var,
                                              command=self.browse_output_folder,
                                              style='Dark.TButton')
        self.output_folder_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Options frame
        options_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Auto-download toggle
        self.auto_download_check = ttk.Checkbutton(options_frame,
                                                  text="Auto-download after processing",
                                                  variable=self.auto_download_var,
                                                  command=self.on_auto_download_toggle,
                                                  style='Dark.TCheckbutton')
        self.auto_download_check.pack(anchor=tk.W)
        
        # API Key frame
        api_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(api_frame, text="Real-Debrid API Key:", style='Dark.TLabel').pack(anchor=tk.W)
        self.api_key_entry = tk.Entry(api_frame, show="*", bg='#333333', fg='#ffffff',
                                     insertbackground='#ffffff')
        self.api_key_entry.pack(fill=tk.X, pady=(5, 0))
        self.api_key_entry.bind('<KeyRelease>', self.on_api_key_change)
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(progress_frame, text="Progress:", style='Dark.TLabel').pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready", style='Dark.TLabel')
        self.progress_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.start_button = ttk.Button(control_frame, text="Start Processing",
                                      command=self.start_processing,
                                      style='Dark.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop",
                                     command=self.stop_processing,
                                     style='Dark.TButton', state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_log_button = ttk.Button(control_frame, text="Clear Log",
                                          command=self.clear_log,
                                          style='Dark.TButton')
        self.clear_log_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Advanced controls frame
        advanced_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        advanced_frame.pack(fill=tk.X, pady=(10, 15))
        
        ttk.Label(advanced_frame, text="Real-Debrid Management:", style='Dark.TLabel').pack(anchor=tk.W)
        
        advanced_buttons_frame = ttk.Frame(advanced_frame, style='Dark.TFrame')
        advanced_buttons_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.account_info_button = ttk.Button(advanced_buttons_frame, text="Account Info",
                                            command=self.get_account_info,
                                            style='Dark.TButton')
        self.account_info_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_button = ttk.Button(advanced_buttons_frame, text="Refresh Torrents",
                                       command=self.refresh_torrents_display,
                                       style='Dark.TButton')
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.duplicates_button = ttk.Button(advanced_buttons_frame, text="Find Duplicates",
                                          command=self.get_duplicate_groups,
                                          style='Dark.TButton')
        self.duplicates_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Live logging area
        log_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Live Logging:", style='Dark.TLabel').pack(anchor=tk.W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15,
                                                  bg='#2a2a2a', fg='#ffffff',
                                                  insertbackground='#ffffff',
                                                  selectbackground='#555555')
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
    def setup_logging_queue(self):
        """Setup the logging queue for thread-safe GUI updates"""
        self.log_queue = queue.Queue()
        self.check_log_queue()
        
    def check_log_queue(self):
        """Check for new log messages and update the GUI"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.master.after(100, self.check_log_queue)
            
    def log_message(self, message):
        """Thread-safe logging method"""
        self.log_queue.put(message)
        
    def browse_input_folder(self):
        """Browse and select input folder"""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder_var.set(folder)
            self.log_message(f"Input folder selected: {folder}")
            self.validate_folders()
            
    def browse_output_folder(self):
        """Browse and select output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)
            self.log_message(f"Output folder selected: {folder}")
            self.validate_folders()
            
    def validate_folders(self):
        """Validate folder selections and enable/disable start button"""
        input_valid = os.path.isdir(self.input_folder_var.get())
        output_valid = os.path.isdir(self.output_folder_var.get())
        api_valid = len(self.api_key_entry.get().strip()) > 0
        
        if input_valid and output_valid and api_valid and not self.processing_var.get():
            self.start_button.configure(state=tk.NORMAL)
        else:
            self.start_button.configure(state=tk.DISABLED)
            
    def on_auto_download_toggle(self):
        """Handle auto-download toggle state change"""
        if self.auto_download_var.get():
            self.log_message("Auto-download enabled - files will be downloaded automatically")
        else:
            self.log_message("Auto-download disabled - files will be added to Real-Debrid only")
            
    def on_api_key_change(self, event=None):
        """Handle API key changes"""
        self.api_key = self.api_key_entry.get().strip()
        self.validate_folders()
        
    def start_processing(self):
        """Start the batch processing in a separate thread"""
        if not self.validate_inputs():
            return
            
        self.processing_var.set(True)
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.progress_var.set(0)
        self.progress_label.configure(text="Starting...")
        
        # Start processing in a separate thread
        self.processing_thread = threading.Thread(target=self.process_files, daemon=True)
        self.processing_thread.start()
        
        self.log_message("Processing started...")
        
    def stop_processing(self):
        """Stop the current processing"""
        self.processing_var.set(False)
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.progress_label.configure(text="Stopped")
        self.log_message("Processing stopped by user")
        
    def validate_inputs(self):
        """Validate all inputs before processing"""
        if not os.path.isdir(self.input_folder_var.get()):
            messagebox.showerror("Error", "Please select a valid input folder")
            return False
            
        if not os.path.isdir(self.output_folder_var.get()):
            messagebox.showerror("Error", "Please select a valid output folder")
            return False
            
        if not self.api_key.strip():
            messagebox.showerror("Error", "Please enter your Real-Debrid API key")
            return False
            
        return True
        
    def process_files(self):
        """Main file processing logic with smart selection"""
        try:
            input_folder = Path(self.input_folder_var.get())
            
            # Scan for files
            self.log_message(f"Scanning folder: {input_folder}")
            all_files = list(input_folder.rglob('*'))
            
            # Apply smart file selection
            selected_files = self.apply_smart_selection(all_files)
            
            if not selected_files:
                self.log_message("No suitable files found for processing")
                self.stop_processing()
                return
                
            self.log_message(f"Found {len(selected_files)} files to process")
            
            # Process files with concurrent workers
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                total_files = len(selected_files)
                completed = 0
                
                for i, file_path in enumerate(selected_files):
                    if not self.processing_var.get():
                        break
                        
                    # Update progress
                    progress = (i / total_files) * 100
                    self.progress_var.set(progress)
                    self.progress_label.configure(text=f"Processing {i+1}/{total_files}")
                    
                    # Submit file for processing
                    future = executor.submit(self.process_single_file, file_path)
                    
                    # Simulate processing time for demo
                    time.sleep(0.5)
                    
                    completed += 1
                    
            self.progress_var.set(100)
            self.progress_label.configure(text="Completed")
            self.log_message(f"Processing completed! {completed} files processed")
            
        except Exception as e:
            self.log_message(f"Error during processing: {str(e)}")
        finally:
            self.stop_processing()
            
    def apply_smart_selection(self, all_files):
        """Apply smart file selection rules"""
        selected_files = []
        
        for file_path in all_files:
            if not file_path.is_file():
                continue
                
            # Check file extension
            ext = file_path.suffix.lower()
            
            # Skip sample files
            if self.smart_selection_rules['skip_samples']:
                if 'sample' in file_path.name.lower():
                    continue
                    
            # Check file size (skip small files likely to be samples)
            try:
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb < self.smart_selection_rules['min_file_size_mb']:
                    if ext not in self.smart_selection_rules['include_subtitles']:
                        continue
            except:
                continue
                
            # Include based on file type preferences
            if (ext in self.smart_selection_rules['prefer_media_types'] or
                ext in self.smart_selection_rules['include_subtitles'] or
                ext in self.smart_selection_rules['include_archives']):
                selected_files.append(file_path)
                
        return selected_files
        
    def process_single_file(self, file_path):
        """Process a single file with Real-Debrid API integration"""
        self.log_message(f"Processing: {file_path.name}")
        
        try:
            # Real API integration
            if file_path.suffix.lower() == '.torrent':
                result = self.process_torrent_file(file_path)
            elif self.is_magnet_link(file_path):
                result = self.process_magnet_link(file_path)
            elif self.is_supported_link(file_path):
                result = self.process_direct_link(file_path)
            else:
                self.log_message(f"Unsupported file type: {file_path.name}")
                return
            
            if result['success']:
                if self.auto_download_var.get():
                    self.download_processed_file(result['data'])
                else:
                    self.log_message(f"Added to Real-Debrid: {file_path.name}")
            else:
                self.log_message(f"Failed to process {file_path.name}: {result['error']}")
                
        except Exception as e:
            self.log_message(f"Error processing {file_path.name}: {str(e)}")
    
    def process_torrent_file(self, file_path):
        """Process torrent file through backend server API or direct Real-Debrid"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'No API key configured'}
            
            # Try backend server first
            try:
                # Read torrent file and encode as base64 for JSON transmission
                with open(file_path, 'rb') as f:
                    torrent_data = f.read()
                
                import base64
                torrent_b64 = base64.b64encode(torrent_data).decode('utf-8')
                
                # Send to backend server which will handle Real-Debrid integration
                data = {
                    'torrent_data': torrent_b64,
                    'filename': file_path.name
                }
                
                response = requests.post(
                    f'{self.server_url}/api/rd/add_torrent',
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        torrent_info = result.get('res', {})
                        self.log_message(f"Torrent added via backend: {torrent_info.get('id')}")
                        self.select_all_files_backend(torrent_info.get('id'))
                        return {'success': True, 'data': torrent_info}
                    else:
                        raise Exception(result.get('error', 'Backend error'))
                else:
                    raise Exception(f'Backend HTTP {response.status_code}')
                    
            except Exception as backend_error:
                self.log_message(f"Backend failed: {backend_error}, trying direct API...")
                
                # Fallback to direct Real-Debrid API
                with open(file_path, 'rb') as f:
                    torrent_data = f.read()
                
                headers = {'Authorization': f'Bearer {self.api_key}'}
                files = {'torrent': torrent_data}
                
                response = requests.put(
                    'https://api.real-debrid.com/rest/1.0/torrents/addTorrent',
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 201:
                    torrent_info = response.json()
                    self.log_message(f"Torrent added via direct API: {torrent_info.get('id')}")
                    self.select_all_files_direct(torrent_info['id'])
                    return {'success': True, 'data': torrent_info}
                else:
                    return {'success': False, 'error': f'Direct API error: {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Processing error: {str(e)}'}
    
    def process_magnet_link(self, file_path):
        """Process magnet link through backend server API or direct Real-Debrid"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'No API key configured'}
            
            # Read magnet link from file
            with open(file_path, 'r', encoding='utf-8') as f:
                magnet_link = f.read().strip()
            
            if not magnet_link.startswith('magnet:'):
                return {'success': False, 'error': 'Invalid magnet link'}
            
            # Try backend server first
            try:
                data = {'magnet': magnet_link}
                
                response = requests.post(
                    f'{self.server_url}/api/rd/add_magnet',
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        torrent_info = result.get('res', {})
                        self.log_message(f"Magnet added via backend: {torrent_info.get('id')}")
                        self.select_all_files_backend(torrent_info.get('id'))
                        return {'success': True, 'data': torrent_info}
                    else:
                        raise Exception(result.get('error', 'Backend error'))
                else:
                    raise Exception(f'Backend HTTP {response.status_code}')
                    
            except Exception as backend_error:
                self.log_message(f"Backend failed: {backend_error}, trying direct API...")
                
                # Fallback to direct Real-Debrid API
                headers = {'Authorization': f'Bearer {self.api_key}'}
                data = {'magnet': magnet_link}
                
                response = requests.post(
                    'https://api.real-debrid.com/rest/1.0/torrents/addMagnet',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 201:
                    torrent_info = response.json()
                    self.log_message(f"Magnet added via direct API: {torrent_info.get('id')}")
                    self.select_all_files_direct(torrent_info['id'])
                    return {'success': True, 'data': torrent_info}
                else:
                    return {'success': False, 'error': f'Direct API error: {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Processing error: {str(e)}'}
    
    def process_direct_link(self, file_path):
        """Process direct download link through backend server API or direct Real-Debrid"""
        try:
            if not self.api_key:
                return {'success': False, 'error': 'No API key configured'}
            
            # Read link from file
            with open(file_path, 'r', encoding='utf-8') as f:
                link = f.read().strip()
            
            # Try backend server first
            try:
                data = {'link': link}
                
                response = requests.post(
                    f'{self.server_url}/api/rd/unrestrict',
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('ok'):
                        link_info = result.get('res', {})
                        self.log_message(f"Link unrestricted via backend: {link_info.get('filename')}")
                        return {'success': True, 'data': link_info}
                    else:
                        raise Exception(result.get('error', 'Backend error'))
                else:
                    raise Exception(f'Backend HTTP {response.status_code}')
                    
            except Exception as backend_error:
                self.log_message(f"Backend failed: {backend_error}, trying direct API...")
                
                # Fallback to direct Real-Debrid API
                headers = {'Authorization': f'Bearer {self.api_key}'}
                data = {'link': link}
                
                response = requests.post(
                    'https://api.real-debrid.com/rest/1.0/unrestrict/link',
                    headers=headers,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    link_info = response.json()
                    self.log_message(f"Link unrestricted via direct API: {link_info.get('filename')}")
                    return {'success': True, 'data': link_info}
                else:
                    return {'success': False, 'error': f'Direct API error: {response.status_code}'}
                
        except requests.RequestException as e:
            return {'success': False, 'error': f'Network error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Processing error: {str(e)}'}
    
    def select_all_files_backend(self, torrent_id):
        """Select all files in a torrent through backend API"""
        try:
            if not torrent_id:
                return
                
            data = {
                'id': torrent_id,
                'files': 'all'
            }
            
            response = requests.post(
                f'{self.server_url}/api/rd/select_files',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.log_message(f"Files selected for torrent: {torrent_id}")
                else:
                    self.log_message(f"Failed to select files: {result.get('error', 'Unknown error')}")
            else:
                self.log_message(f"Failed to select files: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error selecting files: {str(e)}")
    
    def select_all_files_direct(self, torrent_id):
        """Select all files in a torrent via direct Real-Debrid API"""
        try:
            if not torrent_id:
                return
                
            headers = {'Authorization': f'Bearer {self.api_key}'}
            data = {'files': 'all'}
            
            response = requests.post(
                f'https://api.real-debrid.com/rest/1.0/torrents/selectFiles/{torrent_id}',
                headers=headers,
                data=data,
                timeout=30
            )
            
            if response.status_code == 204:
                self.log_message(f"Files selected for torrent (direct): {torrent_id}")
            else:
                self.log_message(f"Failed to select files (direct): {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error selecting files (direct): {str(e)}")
    
    def download_processed_file(self, file_data):
        """Download processed file from Real-Debrid"""
        try:
            download_url = file_data.get('download') or file_data.get('links', [{}])[0].get('download')
            filename = file_data.get('filename', 'download')
            
            if not download_url:
                self.log_message("No download URL available")
                return
            
            # Start download in background thread
            threading.Thread(
                target=self._download_file_worker,
                args=(download_url, filename),
                daemon=True
            ).start()
            
        except Exception as e:
            self.log_message(f"Download setup error: {str(e)}")
    
    def _download_file_worker(self, url, filename):
        """Background worker for downloading files"""
        try:
            output_path = Path(self.output_folder_var.get()) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.log_message(f"Starting download: {filename}")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                self.log_message(f"Downloaded {filename}: {progress:.1f}%")
            
            self.log_message(f"Download completed: {filename}")
            
        except Exception as e:
            self.log_message(f"Download failed for {filename}: {str(e)}")
    
    def get_account_info(self):
        """Get Real-Debrid account information through backend API"""
        try:
            response = requests.get(
                f'{self.server_url}/api/rd/account',
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    info = result.get('info', {})
                    traffic = result.get('traffic', {})
                    self.log_message(f"Account: {info.get('username', 'Unknown')} - Premium: {info.get('type', 'Unknown')}")
                    self.log_message(f"Traffic: {traffic.get('left', 0)} bytes remaining")
                    return result
                else:
                    self.log_message(f"Failed to get account info: {result.get('error', 'Unknown error')}")
            else:
                self.log_message(f"Backend API error: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error getting account info: {str(e)}")
        return None
    
    def list_torrents(self):
        """List all torrents through backend API"""
        try:
            response = requests.get(
                f'{self.server_url}/api/rd/list',
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    torrents = result.get('torrents', [])
                    self.log_message(f"Found {len(torrents)} torrents in Real-Debrid account")
                    return torrents
                else:
                    self.log_message(f"Failed to list torrents: {result.get('error', 'Unknown error')}")
            else:
                self.log_message(f"Backend API error: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error listing torrents: {str(e)}")
        return []
    
    def get_torrent_info(self, torrent_id):
        """Get detailed torrent information through backend API"""
        try:
            response = requests.get(
                f'{self.server_url}/api/rd/torrent_info',
                params={'id': torrent_id},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    info = result.get('info', {})
                    self.log_message(f"Torrent info: {info.get('filename', 'Unknown')} - Status: {info.get('status', 'Unknown')}")
                    return info
                else:
                    self.log_message(f"Failed to get torrent info: {result.get('error', 'Unknown error')}")
            else:
                self.log_message(f"Backend API error: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error getting torrent info: {str(e)}")
        return None
    
    def delete_torrent(self, torrent_id):
        """Delete a torrent through backend API"""
        try:
            data = {'id': torrent_id}
            
            response = requests.post(
                f'{self.server_url}/api/rd/delete',
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    self.log_message(f"Torrent deleted successfully: {torrent_id}")
                    return True
                else:
                    self.log_message(f"Failed to delete torrent: {result.get('error', 'Unknown error')}")
            else:
                self.log_message(f"Backend API error: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error deleting torrent: {str(e)}")
        return False
    
    def get_duplicate_groups(self):
        """Get duplicate file groups through backend API"""
        try:
            response = requests.get(
                f'{self.server_url}/api/rd/dedup',
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    groups = result.get('groups', [])
                    self.log_message(f"Found {len(groups)} duplicate groups")
                    return groups
                else:
                    self.log_message(f"Failed to get duplicates: {result.get('error', 'Unknown error')}")
            else:
                self.log_message(f"Backend API error: {response.status_code}")
                
        except Exception as e:
            self.log_message(f"Error getting duplicates: {str(e)}")
        return []
    
    def refresh_torrents_display(self):
        """Refresh and display current torrents"""
        self.log_message("Refreshing torrents list...")
        torrents = self.list_torrents()
        
        if torrents:
            self.log_message("Current torrents:")
            for i, torrent in enumerate(torrents[:10]):  # Show first 10
                status = torrent.get('status', 'Unknown')
                filename = torrent.get('filename', 'Unknown')
                progress = torrent.get('progress', 0)
                self.log_message(f"  {i+1}. {filename} - {status} ({progress}%)")
            
            if len(torrents) > 10:
                self.log_message(f"  ... and {len(torrents) - 10} more torrents")
        else:
            self.log_message("No torrents found in Real-Debrid account")
    
    def setup_backend_integration(self):
        """Setup integration with backend server"""
        self.log_message("Setting up backend integration...")
        
        # Test connection to backend server
        try:
            response = requests.get(f'{self.server_url}/desktop/status', timeout=5)
            if response.status_code == 200:
                self.log_message("Backend server connection successful")
                return True
            else:
                self.log_message(f"Backend server error: {response.status_code}")
        except requests.RequestException as e:
            self.log_message(f"Cannot connect to backend server: {str(e)}")
            self.log_message("Please ensure the MediaHub server is running on port 8887")
        
        return False
    
    def is_magnet_link(self, file_path):
        """Check if file contains a magnet link"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content.startswith('magnet:')
        except:
            return False
    
    def is_supported_link(self, file_path):
        """Check if file contains a supported download link"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content.startswith(('http://', 'https://', 'ftp://'))
        except:
            return False
            
    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Log cleared")
        
    def run(self):
        """Start the GUI application"""
        self.master.mainloop()

def main():
    """Main entry point for standalone usage"""
    app = RealDebridManager()
    app.run()

if __name__ == "__main__":
    main()
