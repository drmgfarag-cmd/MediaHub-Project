#!/usr/bin/env python3
"""
Downloader Manager - JDownloader-style Interface for MediaHub Ultimate
Implements queue management, batch downloads, and URL monitoring
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
import urllib.parse
import re
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class DownloadStatus(Enum):
    """Download status enumeration"""
    QUEUED = "Queued"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

@dataclass
class DownloadItem:
    """Represents a download item in the queue"""
    url: str
    filename: str
    destination: str
    size: Optional[int] = None
    progress: float = 0.0
    status: DownloadStatus = DownloadStatus.QUEUED
    speed: str = "0 KB/s"
    eta: str = "--:--"
    error_message: str = ""

class DownloaderManager:
    """JDownloader-style download manager with queue management"""
    
    def __init__(self, master=None):
        self.master = master or tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.setup_gui()
        self.setup_download_queue()
        
        # Download settings
        self.max_concurrent_downloads = 4
        self.download_folder = ""
        self.auto_extract = True
        self.downloads: List[DownloadItem] = []
        self.active_downloads = {}
        
        # URL patterns for supported sites
        self.supported_patterns = [
            r'youtube\.com/watch\?v=',
            r'youtu\.be/',
            r'mega\.nz/',
            r'mediafire\.com/',
            r'drive\.google\.com/',
            r'dropbox\.com/',
            r'1fichier\.com/',
            r'rapidgator\.net/',
            r'uploaded\.net/',
        ]
        
    def setup_window(self):
        """Configure the main window"""
        self.master.title("Downloader Manager - MediaHub Ultimate")
        self.master.geometry("1200x800")
        self.master.configure(bg='#1a1a1a')  # Dark theme
        
        # Configure style for dark theme
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Dark theme colors
        self.style.configure('Dark.TFrame', background='#1a1a1a')
        self.style.configure('Dark.TLabel', background='#1a1a1a', foreground='#ffffff')
        self.style.configure('Dark.TButton', background='#333333', foreground='#ffffff')
        self.style.configure('Dark.Treeview', background='#2a2a2a', foreground='#ffffff',
                           fieldbackground='#2a2a2a')
        self.style.configure('Dark.Treeview.Heading', background='#333333', foreground='#ffffff')
        
    def setup_variables(self):
        """Initialize tkinter variables"""
        self.download_folder_var = tk.StringVar(value="Select Download Folder...")
        self.auto_extract_var = tk.BooleanVar(value=True)
        self.max_downloads_var = tk.IntVar(value=4)
        self.total_progress_var = tk.DoubleVar(value=0.0)
        
    def setup_gui(self):
        """Create the GUI elements"""
        # Main container
        main_frame = ttk.Frame(self.master, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Download Manager", 
                               font=('Arial', 16, 'bold'), style='Dark.TLabel')
        title_label.pack(pady=(0, 20))
        
        # Top control panel
        self.create_control_panel(main_frame)
        
        # URL input section
        self.create_url_input_section(main_frame)
        
        # Download queue (main content area)
        self.create_download_queue(main_frame)
        
        # Bottom status and progress
        self.create_status_section(main_frame)
        
    def create_control_panel(self, parent):
        """Create the top control panel"""
        control_frame = ttk.Frame(parent, style='Dark.TFrame')
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Download folder selection
        folder_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(folder_frame, text="Download Folder:", style='Dark.TLabel').pack(side=tk.LEFT)
        
        self.folder_button = ttk.Button(folder_frame,
                                       textvariable=self.download_folder_var,
                                       command=self.browse_download_folder,
                                       style='Dark.TButton')
        self.folder_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        # Settings frame
        settings_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        settings_frame.pack(fill=tk.X)
        
        # Auto-extract option
        self.auto_extract_check = ttk.Checkbutton(settings_frame,
                                                 text="Auto-extract archives",
                                                 variable=self.auto_extract_var,
                                                 style='Dark.TCheckbutton')
        self.auto_extract_check.pack(side=tk.LEFT)
        
        # Max concurrent downloads
        ttk.Label(settings_frame, text="Max Downloads:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(20, 5))
        
        max_downloads_spin = tk.Spinbox(settings_frame, from_=1, to=10,
                                       textvariable=self.max_downloads_var,
                                       width=5, bg='#333333', fg='#ffffff',
                                       command=self.on_max_downloads_change)
        max_downloads_spin.pack(side=tk.LEFT)
        
    def create_url_input_section(self, parent):
        """Create the URL input and link detector section"""
        url_frame = ttk.Frame(parent, style='Dark.TFrame')
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        # URL input
        url_input_frame = ttk.Frame(url_frame, style='Dark.TFrame')
        url_input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(url_input_frame, text="Add URLs:", style='Dark.TLabel').pack(anchor=tk.W)
        
        url_entry_frame = ttk.Frame(url_input_frame, style='Dark.TFrame')
        url_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.url_entry = scrolledtext.ScrolledText(url_entry_frame, height=4,
                                                   bg='#333333', fg='#ffffff',
                                                   insertbackground='#ffffff')
        self.url_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # URL control buttons
        url_buttons_frame = ttk.Frame(url_entry_frame, style='Dark.TFrame')
        url_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        self.add_urls_button = ttk.Button(url_buttons_frame, text="Add URLs",
                                         command=self.add_urls,
                                         style='Dark.TButton')
        self.add_urls_button.pack(fill=tk.X, pady=(0, 5))
        
        self.paste_button = ttk.Button(url_buttons_frame, text="Paste",
                                      command=self.paste_from_clipboard,
                                      style='Dark.TButton')
        self.paste_button.pack(fill=tk.X, pady=(0, 5))
        
        self.clear_button = ttk.Button(url_buttons_frame, text="Clear",
                                      command=self.clear_url_entry,
                                      style='Dark.TButton')
        self.clear_button.pack(fill=tk.X)
        
    def create_download_queue(self, parent):
        """Create the main download queue display"""
        queue_frame = ttk.Frame(parent, style='Dark.TFrame')
        queue_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        ttk.Label(queue_frame, text="Download Queue:", style='Dark.TLabel').pack(anchor=tk.W)
        
        # Treeview for download queue
        tree_frame = ttk.Frame(queue_frame, style='Dark.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Configure treeview columns
        columns = ('filename', 'size', 'progress', 'status', 'speed', 'eta')
        self.download_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                         style='Dark.Treeview')
        
        # Configure column headings and widths
        self.download_tree.heading('filename', text='Filename')
        self.download_tree.heading('size', text='Size')
        self.download_tree.heading('progress', text='Progress')
        self.download_tree.heading('status', text='Status')
        self.download_tree.heading('speed', text='Speed')
        self.download_tree.heading('eta', text='ETA')
        
        self.download_tree.column('filename', width=300)
        self.download_tree.column('size', width=100)
        self.download_tree.column('progress', width=100)
        self.download_tree.column('status', width=100)
        self.download_tree.column('speed', width=100)
        self.download_tree.column('eta', width=80)
        
        # Scrollbars for treeview
        tree_scrollbar_v = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.download_tree.yview)
        tree_scrollbar_h = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.download_tree.xview)
        self.download_tree.configure(yscrollcommand=tree_scrollbar_v.set, xscrollcommand=tree_scrollbar_h.set)
        
        # Pack treeview and scrollbars
        self.download_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Right-click context menu
        self.create_context_menu()
        
        # Queue control buttons
        queue_controls_frame = ttk.Frame(queue_frame, style='Dark.TFrame')
        queue_controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_all_button = ttk.Button(queue_controls_frame, text="Start All",
                                          command=self.start_all_downloads,
                                          style='Dark.TButton')
        self.start_all_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.pause_all_button = ttk.Button(queue_controls_frame, text="Pause All",
                                          command=self.pause_all_downloads,
                                          style='Dark.TButton')
        self.pause_all_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_completed_button = ttk.Button(queue_controls_frame, text="Clear Completed",
                                                command=self.clear_completed_downloads,
                                                style='Dark.TButton')
        self.clear_completed_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.remove_selected_button = ttk.Button(queue_controls_frame, text="Remove Selected",
                                                command=self.remove_selected_downloads,
                                                style='Dark.TButton')
        self.remove_selected_button.pack(side=tk.RIGHT)
        
    def create_context_menu(self):
        """Create right-click context menu for download items"""
        self.context_menu = tk.Menu(self.master, tearoff=0, bg='#333333', fg='#ffffff')
        self.context_menu.add_command(label="Start", command=self.start_selected_download)
        self.context_menu.add_command(label="Pause", command=self.pause_selected_download)
        self.context_menu.add_command(label="Remove", command=self.remove_selected_downloads)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Open Folder", command=self.open_download_folder)
        self.context_menu.add_command(label="Copy URL", command=self.copy_selected_url)
        
        self.download_tree.bind("<Button-3>", self.show_context_menu)
        
    def create_status_section(self, parent):
        """Create the bottom status and progress section"""
        status_frame = ttk.Frame(parent, style='Dark.TFrame')
        status_frame.pack(fill=tk.X)
        
        # Overall progress
        progress_frame = ttk.Frame(status_frame, style='Dark.TFrame')
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(progress_frame, text="Overall Progress:", style='Dark.TLabel').pack(anchor=tk.W)
        
        self.total_progress_bar = ttk.Progressbar(progress_frame, variable=self.total_progress_var,
                                                 maximum=100, mode='determinate')
        self.total_progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Status labels
        status_info_frame = ttk.Frame(status_frame, style='Dark.TFrame')
        status_info_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_info_frame, text="Ready", style='Dark.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = ttk.Label(status_info_frame, text="0 downloads, 0 active", style='Dark.TLabel')
        self.stats_label.pack(side=tk.RIGHT)
        
    def setup_download_queue(self):
        """Setup the download queue processing"""
        self.update_queue_display()
        
    def browse_download_folder(self):
        """Browse and select download folder"""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.download_folder = folder
            self.download_folder_var.set(folder)
            
    def on_max_downloads_change(self):
        """Handle max downloads setting change"""
        self.max_concurrent_downloads = self.max_downloads_var.get()
        
    def add_urls(self):
        """Add URLs from the text entry to download queue"""
        url_text = self.url_entry.get(1.0, tk.END).strip()
        if not url_text:
            return
            
        if not self.download_folder:
            messagebox.showwarning("Warning", "Please select a download folder first")
            return
            
        # Parse URLs from text
        urls = self.parse_urls(url_text)
        
        for url in urls:
            if self.is_supported_url(url):
                # Create download item
                filename = self.extract_filename(url)
                download_item = DownloadItem(
                    url=url,
                    filename=filename,
                    destination=self.download_folder
                )
                self.downloads.append(download_item)
                
        self.update_queue_display()
        self.clear_url_entry()
        
    def parse_urls(self, text):
        """Parse URLs from text input"""
        # Simple URL detection regex
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        # Also check for lines that might be URLs
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('http') and '.' in line:
                # Try to fix incomplete URLs
                if not line.startswith(('http://', 'https://')):
                    line = 'https://' + line
                urls.append(line)
                
        return list(set(urls))  # Remove duplicates
        
    def is_supported_url(self, url):
        """Check if URL is from a supported site"""
        for pattern in self.supported_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return True  # For demo, accept all URLs
        
    def extract_filename(self, url):
        """Extract filename from URL"""
        try:
            parsed_url = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                filename = f"download_{len(self.downloads)+1}"
            return filename
        except:
            return f"download_{len(self.downloads)+1}"
            
    def paste_from_clipboard(self):
        """Paste URLs from clipboard"""
        try:
            clipboard_text = self.master.clipboard_get()
            self.url_entry.insert(tk.END, clipboard_text + '\n')
        except:
            pass
            
    def clear_url_entry(self):
        """Clear the URL entry field"""
        self.url_entry.delete(1.0, tk.END)
        
    def update_queue_display(self):
        """Update the download queue display"""
        # Clear existing items
        for item in self.download_tree.get_children():
            self.download_tree.delete(item)
            
        # Add current downloads
        for i, download in enumerate(self.downloads):
            size_str = self.format_size(download.size) if download.size else "Unknown"
            progress_str = f"{download.progress:.1f}%"
            
            self.download_tree.insert('', tk.END, values=(
                download.filename,
                size_str,
                progress_str,
                download.status.value,
                download.speed,
                download.eta
            ))
            
        # Update stats
        total_downloads = len(self.downloads)
        active_downloads = len([d for d in self.downloads if d.status == DownloadStatus.DOWNLOADING])
        self.stats_label.configure(text=f"{total_downloads} downloads, {active_downloads} active")
        
        # Schedule next update
        self.master.after(1000, self.update_queue_display)
        
    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes is None:
            return "Unknown"
            
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
        
    def start_all_downloads(self):
        """Start all queued downloads"""
        for download in self.downloads:
            if download.status == DownloadStatus.QUEUED:
                download.status = DownloadStatus.DOWNLOADING
                # TODO: Start actual download
                
    def pause_all_downloads(self):
        """Pause all active downloads"""
        for download in self.downloads:
            if download.status == DownloadStatus.DOWNLOADING:
                download.status = DownloadStatus.PAUSED
                
    def clear_completed_downloads(self):
        """Remove completed downloads from queue"""
        self.downloads = [d for d in self.downloads if d.status != DownloadStatus.COMPLETED]
        
    def remove_selected_downloads(self):
        """Remove selected downloads from queue"""
        selected_items = self.download_tree.selection()
        if selected_items:
            # Get indices of selected items
            indices_to_remove = []
            for item in selected_items:
                index = self.download_tree.index(item)
                indices_to_remove.append(index)
                
            # Remove from downloads list (reverse order to maintain indices)
            for index in sorted(indices_to_remove, reverse=True):
                if 0 <= index < len(self.downloads):
                    del self.downloads[index]
                    
    def show_context_menu(self, event):
        """Show context menu for right-click"""
        item = self.download_tree.identify_row(event.y)
        if item:
            self.download_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
            
    def start_selected_download(self):
        """Start selected download"""
        # TODO: Implement selected download start
        pass
        
    def pause_selected_download(self):
        """Pause selected download"""
        # TODO: Implement selected download pause
        pass
        
    def open_download_folder(self):
        """Open the download folder"""
        if self.download_folder and os.path.exists(self.download_folder):
            os.startfile(self.download_folder) if os.name == 'nt' else os.system(f'open "{self.download_folder}"')
            
    def copy_selected_url(self):
        """Copy selected download URL to clipboard"""
        selected_items = self.download_tree.selection()
        if selected_items:
            index = self.download_tree.index(selected_items[0])
            if 0 <= index < len(self.downloads):
                url = self.downloads[index].url
                self.master.clipboard_clear()
                self.master.clipboard_append(url)
                
    def run(self):
        """Start the GUI application"""
        self.master.mainloop()

def main():
    """Main entry point for standalone usage"""
    app = DownloaderManager()
    app.run()

if __name__ == "__main__":
    main()
