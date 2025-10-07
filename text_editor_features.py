#!/usr/bin/env python3
"""
Advanced Text Editor Features
Extended functionality and helper classes
"""

import re
import json
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FindResult:
    """Represents a find/search result"""
    file_path: str
    line_number: int
    column_start: int
    column_end: int
    line_content: str
    match_text: str

@dataclass
class Bookmark:
    """Represents a bookmark in a file"""
    file_path: str
    line_number: int
    description: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MacroRecorder:
    """Records and plays back macro commands"""
    
    def __init__(self):
        self.recording = False
        self.commands = []
        self.current_macro = None
    
    def start_recording(self, name: str = "Macro"):
        """Start recording a macro"""
        self.recording = True
        self.commands = []
        self.current_macro = name
        print(f"Started recording macro: {name}")
    
    def stop_recording(self):
        """Stop recording macro"""
        self.recording = False
        print(f"Stopped recording macro: {self.current_macro} ({len(self.commands)} commands)")
        return self.commands.copy()
    
    def record_command(self, command: str, parameters: dict = None):
        """Record a command"""
        if self.recording:
            self.commands.append({
                'command': command,
                'parameters': parameters or {},
                'timestamp': time.time()
            })
    
    def play_macro(self, commands: List[dict], editor_instance):
        """Play back recorded commands"""
        for cmd in commands:
            try:
                command_name = cmd['command']
                parameters = cmd.get('parameters', {})
                
                # Execute command on editor instance
                if hasattr(editor_instance, command_name):
                    method = getattr(editor_instance, command_name)
                    if callable(method):
                        method(**parameters)
                        time.sleep(0.1)  # Small delay between commands
                        
            except Exception as e:
                print(f"Error executing macro command {cmd}: {e}")
                break

class FileSearcher:
    """Advanced file searching functionality"""
    
    def __init__(self):
        self.search_results = []
        self.search_thread = None
        self.stop_search = False
    
    def search_in_files(
        self,
        search_term: str,
        directory: str,
        file_patterns: List[str] = None,
        case_sensitive: bool = False,
        regex: bool = False,
        whole_word: bool = False,
        include_subdirectories: bool = True
    ) -> List[FindResult]:
        """Search for text in multiple files"""
        
        if file_patterns is None:
            file_patterns = ['*.*']
        
        results = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return results
        
        # Prepare search pattern
        if regex:
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(search_term, flags)
            except re.error as e:
                print(f"Invalid regex pattern: {e}")
                return results
        else:
            if whole_word:
                search_term = f"\\b{re.escape(search_term)}\\b"
            else:
                search_term = re.escape(search_term)
            
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(search_term, flags)
        
        # Find files to search
        files_to_search = []
        
        for pattern_str in file_patterns:
            if include_subdirectories:
                files_to_search.extend(directory_path.rglob(pattern_str))
            else:
                files_to_search.extend(directory_path.glob(pattern_str))
        
        # Remove duplicates and filter files
        files_to_search = list(set(f for f in files_to_search if f.is_file()))
        
        # Search in each file
        for file_path in files_to_search:
            if self.stop_search:
                break
                
            try:
                # Try different encodings
                content = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    continue
                
                # Search for matches
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    matches = pattern.finditer(line)
                    for match in matches:
                        result = FindResult(
                            file_path=str(file_path),
                            line_number=line_num,
                            column_start=match.start(),
                            column_end=match.end(),
                            line_content=line,
                            match_text=match.group()
                        )
                        results.append(result)
                        
            except Exception as e:
                print(f"Error searching in {file_path}: {e}")
                continue
        
        return results
    
    def start_async_search(self, *args, **kwargs):
        """Start search in background thread"""
        self.stop_search = False
        self.search_thread = threading.Thread(
            target=self._async_search_worker,
            args=args,
            kwargs=kwargs
        )
        self.search_thread.start()
    
    def _async_search_worker(self, *args, **kwargs):
        """Background search worker"""
        self.search_results = self.search_in_files(*args, **kwargs)
    
    def stop_async_search(self):
        """Stop background search"""
        self.stop_search = True
        if self.search_thread and self.search_thread.is_alive():
            self.search_thread.join(timeout=1.0)

class BookmarkManager:
    """Manages bookmarks across files"""
    
    def __init__(self):
        self.bookmarks: Dict[str, List[Bookmark]] = {}
        self.bookmark_file = Path("bookmarks.json")
        self.load_bookmarks()
    
    def add_bookmark(self, file_path: str, line_number: int, description: str = ""):
        """Add a bookmark"""
        bookmark = Bookmark(file_path, line_number, description)
        
        if file_path not in self.bookmarks:
            self.bookmarks[file_path] = []
        
        # Remove existing bookmark at same line
        self.bookmarks[file_path] = [
            b for b in self.bookmarks[file_path] 
            if b.line_number != line_number
        ]
        
        self.bookmarks[file_path].append(bookmark)
        self.bookmarks[file_path].sort(key=lambda b: b.line_number)
        self.save_bookmarks()
    
    def remove_bookmark(self, file_path: str, line_number: int):
        """Remove a bookmark"""
        if file_path in self.bookmarks:
            self.bookmarks[file_path] = [
                b for b in self.bookmarks[file_path] 
                if b.line_number != line_number
            ]
            if not self.bookmarks[file_path]:
                del self.bookmarks[file_path]
            self.save_bookmarks()
    
    def toggle_bookmark(self, file_path: str, line_number: int, description: str = ""):
        """Toggle bookmark at line"""
        if self.has_bookmark(file_path, line_number):
            self.remove_bookmark(file_path, line_number)
            return False
        else:
            self.add_bookmark(file_path, line_number, description)
            return True
    
    def has_bookmark(self, file_path: str, line_number: int) -> bool:
        """Check if line has bookmark"""
        if file_path in self.bookmarks:
            return any(b.line_number == line_number for b in self.bookmarks[file_path])
        return False
    
    def get_bookmarks(self, file_path: str) -> List[Bookmark]:
        """Get bookmarks for file"""
        return self.bookmarks.get(file_path, [])
    
    def get_all_bookmarks(self) -> Dict[str, List[Bookmark]]:
        """Get all bookmarks"""
        return self.bookmarks.copy()
    
    def get_next_bookmark(self, file_path: str, current_line: int) -> Optional[Bookmark]:
        """Get next bookmark after current line"""
        bookmarks = self.get_bookmarks(file_path)
        for bookmark in bookmarks:
            if bookmark.line_number > current_line:
                return bookmark
        # Wrap around to first bookmark
        return bookmarks[0] if bookmarks else None
    
    def get_previous_bookmark(self, file_path: str, current_line: int) -> Optional[Bookmark]:
        """Get previous bookmark before current line"""
        bookmarks = self.get_bookmarks(file_path)
        for bookmark in reversed(bookmarks):
            if bookmark.line_number < current_line:
                return bookmark
        # Wrap around to last bookmark
        return bookmarks[-1] if bookmarks else None
    
    def save_bookmarks(self):
        """Save bookmarks to file"""
        try:
            data = {}
            for file_path, bookmarks in self.bookmarks.items():
                data[file_path] = [
                    {
                        'line_number': b.line_number,
                        'description': b.description,
                        'timestamp': b.timestamp.isoformat()
                    }
                    for b in bookmarks
                ]
            
            with open(self.bookmark_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving bookmarks: {e}")
    
    def load_bookmarks(self):
        """Load bookmarks from file"""
        try:
            if not self.bookmark_file.exists():
                return
                
            with open(self.bookmark_file, 'r') as f:
                data = json.load(f)
            
            self.bookmarks = {}
            for file_path, bookmark_data in data.items():
                self.bookmarks[file_path] = [
                    Bookmark(
                        file_path=file_path,
                        line_number=b['line_number'],
                        description=b.get('description', ''),
                        timestamp=datetime.fromisoformat(b['timestamp'])
                    )
                    for b in bookmark_data
                ]
                
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            self.bookmarks = {}

class SyntaxHighlighter:
    """Custom syntax highlighting for Monaco Editor"""
    
    def __init__(self):
        self.language_configs = self._load_language_configs()
    
    def _load_language_configs(self) -> Dict[str, dict]:
        """Load language configuration for syntax highlighting"""
        return {
            'python': {
                'keywords': [
                    'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
                    'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
                    'from', 'global', 'if', 'import', 'in', 'is', 'lambda',
                    'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
                    'while', 'with', 'yield', 'async', 'await'
                ],
                'builtins': [
                    'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes',
                    'chr', 'classmethod', 'compile', 'complex', 'dict', 'dir',
                    'divmod', 'enumerate', 'eval', 'filter', 'float', 'format',
                    'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help',
                    'hex', 'id', 'input', 'int', 'isinstance', 'issubclass',
                    'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview',
                    'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
                    'property', 'range', 'repr', 'reversed', 'round', 'set',
                    'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
                    'super', 'tuple', 'type', 'vars', 'zip'
                ],
                'operators': [
                    '+', '-', '*', '/', '//', '%', '**', '=', '+=', '-=',
                    '*=', '/=', '//=', '%=', '**=', '==', '!=', '<', '>',
                    '<=', '>=', '&', '|', '^', '~', '<<', '>>', '&=', '|=',
                    '^=', '<<=' '>>='
                ],
                'delimiters': ['(', ')', '[', ']', '{', '}', ',', ':', ';', '.'],
                'comments': {'line': '#', 'block': ["'''", '"""']}
            },
            'javascript': {
                'keywords': [
                    'break', 'case', 'catch', 'class', 'const', 'continue',
                    'debugger', 'default', 'delete', 'do', 'else', 'export',
                    'extends', 'finally', 'for', 'function', 'if', 'import',
                    'in', 'instanceof', 'let', 'new', 'return', 'super',
                    'switch', 'this', 'throw', 'try', 'typeof', 'var',
                    'void', 'while', 'with', 'yield', 'async', 'await'
                ],
                'builtins': [
                    'Array', 'Boolean', 'Date', 'Error', 'Function', 'Number',
                    'Object', 'RegExp', 'String', 'Symbol', 'console', 'window',
                    'document', 'Math', 'JSON', 'Promise', 'Set', 'Map',
                    'WeakSet', 'WeakMap', 'Proxy', 'Reflect'
                ],
                'comments': {'line': '//', 'block': ['/*', '*/']}
            }
        }
    
    def get_language_config(self, language: str) -> dict:
        """Get configuration for a specific language"""
        return self.language_configs.get(language.lower(), {})
    
    def add_language_config(self, language: str, config: dict):
        """Add or update language configuration"""
        self.language_configs[language.lower()] = config

class DocumentStatistics:
    """Calculate document statistics"""
    
    @staticmethod
    def analyze_text(content: str) -> dict:
        """Analyze text content and return statistics"""
        if not content:
            return {
                'characters': 0,
                'characters_no_spaces': 0,
                'words': 0,
                'lines': 0,
                'paragraphs': 0,
                'sentences': 0
            }
        
        # Basic counts
        characters = len(content)
        characters_no_spaces = len(content.replace(' ', '').replace('\t', ''))
        lines = len(content.split('\n'))
        
        # Word count (split by whitespace)
        words = len(content.split())
        
        # Paragraph count (separated by double newlines)
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])
        
        # Sentence count (basic - counts periods, exclamations, questions)
        sentences = len(re.findall(r'[.!?]+', content))
        
        return {
            'characters': characters,
            'characters_no_spaces': characters_no_spaces,
            'words': words,
            'lines': lines,
            'paragraphs': paragraphs,
            'sentences': sentences
        }
    
    @staticmethod
    def get_reading_time(word_count: int, words_per_minute: int = 200) -> float:
        """Calculate estimated reading time in minutes"""
        return word_count / words_per_minute if word_count > 0 else 0
    
    @staticmethod
    def get_language_stats(content: str, language: str) -> dict:
        """Get language-specific statistics"""
        stats = {'language': language}
        
        if language.lower() == 'python':
            # Python-specific stats
            stats.update({
                'imports': len(re.findall(r'^\s*(?:import|from)\s+', content, re.MULTILINE)),
                'functions': len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE)),
                'classes': len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE)),
                'comments': len(re.findall(r'#.*$', content, re.MULTILINE)),
                'docstrings': len(re.findall(r'"""[\s\S]*?"""', content))
            })
        
        elif language.lower() == 'javascript':
            # JavaScript-specific stats
            stats.update({
                'functions': len(re.findall(r'function\s+\w+|\w+\s*=\s*function|\w+\s*=>|async\s+function', content)),
                'classes': len(re.findall(r'class\s+\w+', content)),
                'comments': len(re.findall(r'//.*$|/\*[\s\S]*?\*/', content, re.MULTILINE)),
                'imports': len(re.findall(r'import\s+.*?from|require\s*\(', content))
            })
        
        return stats

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def detect_line_endings(content: str) -> str:
    """Detect line ending style in content"""
    crlf_count = content.count('\r\n')
    lf_count = content.count('\n') - crlf_count
    cr_count = content.count('\r') - crlf_count
    
    if crlf_count > lf_count and crlf_count > cr_count:
        return 'CRLF'
    elif cr_count > lf_count and cr_count > crlf_count:
        return 'CR'
    else:
        return 'LF'

def normalize_line_endings(content: str, target: str = 'LF') -> str:
    """Normalize line endings in content"""
    # First normalize to LF
    content = content.replace('\r\n', '\n').replace('\r', '\n')
    
    # Then convert to target format
    if target == 'CRLF':
        content = content.replace('\n', '\r\n')
    elif target == 'CR':
        content = content.replace('\n', '\r')
    
    return content
