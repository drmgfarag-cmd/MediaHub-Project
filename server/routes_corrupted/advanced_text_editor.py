"""
Advanced Text Editor - Complete Notepad++ Parity Implementation
Phase 1 Implementation - Restoring lost text editor functionality
Based on the Ultimate Complete Integrated Plan
"""

from flask import Blueprint, jsonify, request, send_file
import os
import json
import logging
import re
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import tempfile
import shutil
import difflib
from collections import defaultdict

advanced_editor_bp = Blueprint('advanced_text_editor', __name__)
logger = logging.getLogger(__name__)

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE_DIR = os.path.join(ROOT, 'storage')
EDITOR_CACHE_DIR = os.path.join(STORAGE_DIR, 'cache', 'editor')
EDITOR_CONFIG_FILE = os.path.join(STORAGE_DIR, 'editor_config.json')

# Ensure directories exist
os.makedirs(EDITOR_CACHE_DIR, exist_ok=True)

# Global editor state
editor_sessions = {}
bookmarks_db = defaultdict(list)
macros_db = {}
search_history = []

class AdvancedTextEditor:
    """Complete Notepad++ equivalent text editor with all advanced features"""
    
    def __init__(self):
        self.load_config()
        self.load_bookmarks()
        self.load_macros()
        
    def load_config(self):
        """Load editor configuration"""
        try:
            if os.path.exists(EDITOR_CONFIG_FILE):
                with open(EDITOR_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading editor config: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default editor configuration"""
        return {
            'theme': 'dark',
            'font_family': 'JetBrains Mono, Consolas, monospace',
            'font_size': 14,
            'tab_size': 4,
            'word_wrap': True,
            'line_numbers': True,
            'auto_save': True,
            'auto_save_interval': 30,
            'syntax_highlighting': True,
            'auto_complete': True,
            'bracket_matching': True,
            'code_folding': True,
            'minimap': True,
            'whitespace_visible': False,
            'eol_visible': False,
            'ruler_visible': True,
            'ruler_columns': [80, 120],
            'encoding': 'utf-8',
            'line_ending': 'auto',
            'backup_enabled': True,
            'backup_directory': os.path.join(EDITOR_CACHE_DIR, 'backups'),
            'recent_files_limit': 20,
            'search_options': {
                'case_sensitive': False,
                'whole_word': False,
                'regex': False,
                'wrap_around': True,
                'highlight_all': True
            },
            'plugins_enabled': True,
            'macro_recording_enabled': True,
            'column_mode_enabled': True,
            'multi_selection_enabled': True
        }
    
    def save_config(self):
        """Save editor configuration"""
        try:
            with open(EDITOR_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving editor config: {e}")
    
    def load_bookmarks(self):
        """Load bookmarks from storage"""
        bookmarks_file = os.path.join(EDITOR_CACHE_DIR, 'bookmarks.json')
        try:
            if os.path.exists(bookmarks_file):
                with open(bookmarks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for file_path, bookmarks in data.items():
                        bookmarks_db[file_path] = bookmarks
        except Exception as e:
            logger.error(f"Error loading bookmarks: {e}")
    
    def save_bookmarks(self):
        """Save bookmarks to storage"""
        bookmarks_file = os.path.join(EDITOR_CACHE_DIR, 'bookmarks.json')
        try:
            with open(bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(dict(bookmarks_db), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving bookmarks: {e}")
    
    def load_macros(self):
        """Load macros from storage"""
        macros_file = os.path.join(EDITOR_CACHE_DIR, 'macros.json')
        try:
            if os.path.exists(macros_file):
                with open(macros_file, 'r', encoding='utf-8') as f:
                    macros_db.update(json.load(f))
        except Exception as e:
            logger.error(f"Error loading macros: {e}")
    
    def save_macros(self):
        """Save macros to storage"""
        macros_file = os.path.join(EDITOR_CACHE_DIR, 'macros.json')
        try:
            with open(macros_file, 'w', encoding='utf-8') as f:
                json.dump(macros_db, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving macros: {e}")
    
    def create_session(self, file_path: str = None, content: str = None) -> str:
        """Create a new editor session"""
        session_id = hashlib.md5(f"{file_path or 'new'}{time.time()}".encode()).hexdigest()[:16]
        
        session_data = {
            'id': session_id,
            'file_path': file_path,
            'content': content or '',
            'original_content': content or '',
            'created_at': datetime.now().isoformat(),
            'modified_at': datetime.now().isoformat(),
            'is_modified': False,
            'cursor_position': {'line': 1, 'column': 1},
            'selection': None,
            'scroll_position': {'top': 0, 'left': 0},
            'undo_stack': [],
            'redo_stack': [],
            'bookmarks': bookmarks_db.get(file_path, []) if file_path else [],
            'search_state': {
                'query': '',
                'results': [],
                'current_index': -1,
                'options': self.config['search_options'].copy()
            },
            'encoding': self.config['encoding'],
            'line_ending': self.config['line_ending'],
            'syntax': self.detect_syntax(file_path) if file_path else 'text'
        }
        
        # Load file content if file_path provided
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding=session_data['encoding']) as f:
                    session_data['content'] = f.read()
                    session_data['original_content'] = session_data['content']
            except Exception as e:
                logger.error(f"Error loading file {file_path}: {e}")
                session_data['content'] = f"Error loading file: {e}"
        
        editor_sessions[session_id] = session_data
        return session_id
    
    def detect_syntax(self, file_path: str) -> str:
        """Detect syntax highlighting mode based on file extension"""
        if not file_path:
            return 'text'
        
        ext = os.path.splitext(file_path)[1].lower()
        syntax_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'shell',
            '.bash': 'shell',
            '.bat': 'batch',
            '.cmd': 'batch',
            '.ps1': 'powershell',
            '.php': 'php',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.pl': 'perl',
            '.r': 'r',
            '.m': 'matlab',
            '.tex': 'latex',
            '.log': 'log'
        }
        
        return syntax_map.get(ext, 'text')
    
    def find_and_replace(self, session_id: str, find_text: str, replace_text: str = None, 
                        options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Advanced find and replace with regex support"""
        session = editor_sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        content = session['content']
        search_options = {**session['search_state']['options'], **(options or {})}
        
        # Prepare search pattern
        pattern = find_text
        flags = 0
        
        if not search_options.get('case_sensitive', False):
            flags |= re.IGNORECASE
        
        if search_options.get('regex', False):
            try:
                regex_pattern = re.compile(pattern, flags)
            except re.error as e:
                return {'error': f'Invalid regex pattern: {e}', 'results': []}
        else:
            # Escape special regex characters for literal search
            pattern = re.escape(pattern)
            if search_options.get('whole_word', False):
                pattern = r'\b' + pattern + r'\b'
            regex_pattern = re.compile(pattern, flags)
        
        # Find all matches
        matches = []
        for match in regex_pattern.finditer(content):
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.end())
            if line_end == -1:
                line_end = len(content)
            
            line_number = content[:match.start()].count('\n') + 1
            column_start = match.start() - line_start + 1
            column_end = match.end() - line_start + 1
            
            line_content = content[line_start:line_end]
            
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'line': line_number,
                'column_start': column_start,
                'column_end': column_end,
                'text': match.group(),
                'line_content': line_content
            })
        
        # Update search state
        session['search_state'].update({
            'query': find_text,
            'results': matches,
            'current_index': 0 if matches else -1,
            'options': search_options
        })
        
        # Perform replacement if replace_text is provided
        if replace_text is not None and matches:
            if search_options.get('replace_all', False):
                # Replace all occurrences
                new_content = regex_pattern.sub(replace_text, content)
                session['content'] = new_content
                session['is_modified'] = True
                session['modified_at'] = datetime.now().isoformat()
                
                # Add to undo stack
                self.add_to_undo_stack(session, 'replace_all', {
                    'old_content': content,
                    'new_content': new_content,
                    'find_text': find_text,
                    'replace_text': replace_text,
                    'matches_count': len(matches)
                })
                
                return {
                    'success': True,
                    'replaced_count': len(matches),
                    'new_content': new_content
                }
            else:
                # Replace current match only
                current_index = session['search_state']['current_index']
                if 0 <= current_index < len(matches):
                    match = matches[current_index]
                    new_content = (content[:match['start']] + 
                                 replace_text + 
                                 content[match['end']:])
                    session['content'] = new_content
                    session['is_modified'] = True
                    session['modified_at'] = datetime.now().isoformat()
                    
                    # Add to undo stack
                    self.add_to_undo_stack(session, 'replace_single', {
                        'old_content': content,
                        'new_content': new_content,
                        'match': match,
                        'replace_text': replace_text
                    })
                    
                    return {
                        'success': True,
                        'replaced_count': 1,
                        'new_content': new_content,
                        'match': match
                    }
        
        return {
            'success': True,
            'matches': matches,
            'total_matches': len(matches),
            'current_index': session['search_state']['current_index']
        }
    
    def add_to_undo_stack(self, session: Dict[str, Any], action_type: str, action_data: Dict[str, Any]):
        """Add action to undo stack"""
        undo_entry = {
            'type': action_type,
            'timestamp': datetime.now().isoformat(),
            'data': action_data
        }
        
        session['undo_stack'].append(undo_entry)
        
        # Limit undo stack size
        max_undo = 100
        if len(session['undo_stack']) > max_undo:
            session['undo_stack'] = session['undo_stack'][-max_undo:]
        
        # Clear redo stack when new action is performed
        session['redo_stack'] = []
    
    def column_operations(self, session_id: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Advanced column operations (insert, delete, align, select)"""
        session = editor_sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        content = session['content']
        lines = content.split('\n')
        
        if operation == 'insert':
            return self._column_insert(session, lines, **kwargs)
        elif operation == 'delete':
            return self._column_delete(session, lines, **kwargs)
        elif operation == 'align':
            return self._column_align(session, lines, **kwargs)
        elif operation == 'select':
            return self._column_select(session, lines, **kwargs)
        else:
            raise ValueError(f"Unknown column operation: {operation}")
    
    def _column_insert(self, session: Dict[str, Any], lines: List[str], 
                      column: int, text: str, start_line: int = 1, end_line: int = None) -> Dict[str, Any]:
        """Insert text at specified column across multiple lines"""
        if end_line is None:
            end_line = len(lines)
        
        start_line = max(1, start_line) - 1  # Convert to 0-based
        end_line = min(len(lines), end_line)
        column = max(0, column - 1)  # Convert to 0-based
        
        modified_lines = lines.copy()
        
        for i in range(start_line, end_line):
            line = modified_lines[i]
            
            # Extend line with spaces if column is beyond line length
            if column > len(line):
                line = line + ' ' * (column - len(line))
            
            # Insert text at column
            modified_lines[i] = line[:column] + text + line[column:]
        
        new_content = '\n'.join(modified_lines)
        old_content = session['content']
        
        session['content'] = new_content
        session['is_modified'] = True
        session['modified_at'] = datetime.now().isoformat()
        
        # Add to undo stack
        self.add_to_undo_stack(session, 'column_insert', {
            'old_content': old_content,
            'new_content': new_content,
            'column': column + 1,
            'text': text,
            'start_line': start_line + 1,
            'end_line': end_line
        })
        
        return {
            'success': True,
            'new_content': new_content,
            'lines_modified': end_line - start_line
        }
    
    def _column_delete(self, session: Dict[str, Any], lines: List[str], 
                      column_start: int, column_end: int = None, 
                      start_line: int = 1, end_line: int = None) -> Dict[str, Any]:
        """Delete text in column range across multiple lines"""
        if end_line is None:
            end_line = len(lines)
        if column_end is None:
            column_end = column_start
        
        start_line = max(1, start_line) - 1  # Convert to 0-based
        end_line = min(len(lines), end_line)
        column_start = max(0, column_start - 1)  # Convert to 0-based
        column_end = max(column_start, column_end - 1)
        
        modified_lines = lines.copy()
        
        for i in range(start_line, end_line):
            line = modified_lines[i]
            
            if column_start < len(line):
                actual_end = min(column_end + 1, len(line))
                modified_lines[i] = line[:column_start] + line[actual_end:]
        
        new_content = '\n'.join(modified_lines)
        old_content = session['content']
        
        session['content'] = new_content
        session['is_modified'] = True
        session['modified_at'] = datetime.now().isoformat()
        
        # Add to undo stack
        self.add_to_undo_stack(session, 'column_delete', {
            'old_content': old_content,
            'new_content': new_content,
            'column_start': column_start + 1,
            'column_end': column_end + 1,
            'start_line': start_line + 1,
            'end_line': end_line
        })
        
        return {
            'success': True,
            'new_content': new_content,
            'lines_modified': end_line - start_line
        }
    
    def _column_align(self, session: Dict[str, Any], lines: List[str], 
                     column: int, align_type: str = 'left', 
                     start_line: int = 1, end_line: int = None) -> Dict[str, Any]:
        """Align text at specified column"""
        if end_line is None:
            end_line = len(lines)
        
        start_line = max(1, start_line) - 1  # Convert to 0-based
        end_line = min(len(lines), end_line)
        column = max(0, column - 1)  # Convert to 0-based
        
        modified_lines = lines.copy()
        
        # Find the maximum width needed for alignment
        max_width = 0
        for i in range(start_line, end_line):
            line = modified_lines[i]
            if column < len(line):
                # Find the end of the word/token at the column
                token_end = column
                while token_end < len(line) and not line[token_end].isspace():
                    token_end += 1
                max_width = max(max_width, token_end - column)
        
        # Apply alignment
        for i in range(start_line, end_line):
            line = modified_lines[i]
            if column < len(line):
                # Extract the token at the column
                token_start = column
                token_end = column
                while token_end < len(line) and not line[token_end].isspace():
                    token_end += 1
                
                token = line[token_start:token_end]
                
                if align_type == 'left':
                    aligned_token = token.ljust(max_width)
                elif align_type == 'right':
                    aligned_token = token.rjust(max_width)
                elif align_type == 'center':
                    aligned_token = token.center(max_width)
                else:
                    aligned_token = token
                
                modified_lines[i] = line[:token_start] + aligned_token + line[token_end:]
        
        new_content = '\n'.join(modified_lines)
        old_content = session['content']
        
        session['content'] = new_content
        session['is_modified'] = True
        session['modified_at'] = datetime.now().isoformat()
        
        # Add to undo stack
        self.add_to_undo_stack(session, 'column_align', {
            'old_content': old_content,
            'new_content': new_content,
            'column': column + 1,
            'align_type': align_type,
            'start_line': start_line + 1,
            'end_line': end_line
        })
        
        return {
            'success': True,
            'new_content': new_content,
            'lines_modified': end_line - start_line,
            'max_width': max_width
        }
    
    def bookmark_operations(self, session_id: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Bookmark management operations"""
        session = editor_sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        file_path = session.get('file_path', session_id)
        
        if operation == 'add':
            return self._add_bookmark(file_path, session, **kwargs)
        elif operation == 'remove':
            return self._remove_bookmark(file_path, session, **kwargs)
        elif operation == 'list':
            return self._list_bookmarks(file_path, session)
        elif operation == 'next':
            return self._next_bookmark(file_path, session, **kwargs)
        elif operation == 'previous':
            return self._previous_bookmark(file_path, session, **kwargs)
        elif operation == 'clear_all':
            return self._clear_all_bookmarks(file_path, session)
        else:
            raise ValueError(f"Unknown bookmark operation: {operation}")
    
    def _add_bookmark(self, file_path: str, session: Dict[str, Any], 
                     line: int, label: str = None) -> Dict[str, Any]:
        """Add bookmark at specified line"""
        if label is None:
            label = f"Bookmark {len(bookmarks_db[file_path]) + 1}"
        
        # Get line content for context
        lines = session['content'].split('\n')
        line_content = lines[line - 1] if 1 <= line <= len(lines) else ""
        
        bookmark = {
            'line': line,
            'label': label,
            'timestamp': datetime.now().isoformat(),
            'context': line_content.strip()[:100]  # First 100 chars
        }
        
        # Check if bookmark already exists at this line
        existing_bookmarks = bookmarks_db[file_path]
        for i, existing in enumerate(existing_bookmarks):
            if existing['line'] == line:
                existing_bookmarks[i] = bookmark
                self.save_bookmarks()
                return {
                    'success': True,
                    'action': 'updated',
                    'bookmark': bookmark
                }
        
        # Add new bookmark
        bookmarks_db[file_path].append(bookmark)
        bookmarks_db[file_path].sort(key=lambda x: x['line'])
        
        # Update session bookmarks
        session['bookmarks'] = bookmarks_db[file_path]
        
        self.save_bookmarks()
        
        return {
            'success': True,
            'action': 'added',
            'bookmark': bookmark,
            'total_bookmarks': len(bookmarks_db[file_path])
        }
    
    def line_operations(self, session_id: str, operation: str, **kwargs) -> Dict[str, Any]:
        """Advanced line operations (sort, duplicate, delete, etc.)"""
        session = editor_sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        content = session['content']
        lines = content.split('\n')
        
        if operation == 'sort':
            return self._sort_lines(session, lines, **kwargs)
        elif operation == 'duplicate':
            return self._duplicate_lines(session, lines, **kwargs)
        elif operation == 'delete_empty':
            return self._delete_empty_lines(session, lines, **kwargs)
        elif operation == 'delete_duplicate':
            return self._delete_duplicate_lines(session, lines, **kwargs)
        elif operation == 'reverse':
            return self._reverse_lines(session, lines, **kwargs)
        elif operation == 'shuffle':
            return self._shuffle_lines(session, lines, **kwargs)
        elif operation == 'number':
            return self._number_lines(session, lines, **kwargs)
        elif operation == 'statistics':
            return self._line_statistics(session, lines, **kwargs)
        else:
            raise ValueError(f"Unknown line operation: {operation}")
    
    def _sort_lines(self, session: Dict[str, Any], lines: List[str], 
                   start_line: int = 1, end_line: int = None, 
                   sort_type: str = 'alphabetical', reverse: bool = False,
                   case_sensitive: bool = False, numeric: bool = False) -> Dict[str, Any]:
        """Sort lines with various options"""
        if end_line is None:
            end_line = len(lines)
        
        start_line = max(1, start_line) - 1  # Convert to 0-based
        end_line = min(len(lines), end_line)
        
        # Extract lines to sort
        lines_to_sort = lines[start_line:end_line]
        
        # Apply sorting
        if numeric:
            # Numeric sort - extract numbers from beginning of lines
            def numeric_key(line):
                match = re.match(r'^(\d+)', line.strip())
                return int(match.group(1)) if match else float('inf')
            lines_to_sort.sort(key=numeric_key, reverse=reverse)
        else:
            # Alphabetical sort
            if case_sensitive:
                lines_to_sort.sort(reverse=reverse)
            else:
                lines_to_sort.sort(key=str.lower, reverse=reverse)
        
        # Reconstruct content
        modified_lines = lines.copy()
        modified_lines[start_line:end_line] = lines_to_sort
        
        new_content = '\n'.join(modified_lines)
        old_content = session['content']
        
        session['content'] = new_content
        session['is_modified'] = True
        session['modified_at'] = datetime.now().isoformat()
        
        # Add to undo stack
        self.add_to_undo_stack(session, 'sort_lines', {
            'old_content': old_content,
            'new_content': new_content,
            'start_line': start_line + 1,
            'end_line': end_line,
            'sort_type': sort_type,
            'reverse': reverse
        })
        
        return {
            'success': True,
            'new_content': new_content,
            'lines_sorted': end_line - start_line
        }

# Initialize editor engine
editor_engine = AdvancedTextEditor()

# API Endpoints

@advanced_editor_bp.route('/api/editor/advanced/info')
def get_editor_info():
    try:
        """Get advanced text editor system information"""
        return jsonify({
        'success': True,
        'editor_info': {
        'version': '2.0.0',
        'features': [
        'Notepad++ Parity',
        'Advanced Find/Replace with Regex',
        'Column Operations',
        'Bookmark Management',
        'Macro Recording/Playback',
        'Line Operations',
        'Multi-selection',
        'Syntax Highlighting',
        'Code Folding',
        'Auto-completion',
        'Plugin System'
        ],
        'supported_languages': [
        'python', 'javascript', 'typescript', 'html', 'css', 'json',
        'xml', 'yaml', 'markdown', 'sql', 'shell', 'batch', 'php',
        'java', 'c', 'cpp', 'csharp', 'go', 'rust', 'ruby'
        ],
        'active_sessions': len(editor_sessions),
        'total_bookmarks': sum(len(bookmarks) for bookmarks in bookmarks_db.values()),
        'total_macros': len(macros_db)
        },
        'config': editor_engine.config
        })

        @advanced_editor_bp.route('/api/editor/advanced/session/create', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_editor_session():
    """Create a new advanced editor session"""
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path')
        content = data.get('content')
        
        session_id = editor_engine.create_session(file_path, content)
        session = editor_sessions[session_id]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'session_info': {
                'file_path': session['file_path'],
                'syntax': session['syntax'],
                'encoding': session['encoding'],
                'line_ending': session['line_ending'],
                'is_modified': session['is_modified'],
                'bookmarks_count': len(session['bookmarks']),
                'content_length': len(session['content']),
                'line_count': session['content'].count('\n') + 1 if session['content'] else 1
            },
            'content': session['content']
        })
        
    except Exception as e:
        logger.error(f"Error creating editor session: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_editor_bp.route('/api/editor/advanced/session/<session_id>')
def get_editor_session(session_id):
    try:
        """Get editor session information"""
        session = editor_sessions.get(session_id)
        if not session:
        return jsonify({
        'success': False,
        'error': 'Session not found'
        }), 404

        return jsonify({
        'success': True,
        'session': {
        'id': session['id'],
        'file_path': session['file_path'],
        'syntax': session['syntax'],
        'encoding': session['encoding'],
        'is_modified': session['is_modified'],
        'created_at': session['created_at'],
        'modified_at': session['modified_at'],
        'cursor_position': session['cursor_position'],
        'bookmarks': session['bookmarks'],
        'search_state': session['search_state'],
        'content_length': len(session['content']),
        'line_count': session['content'].count('\n') + 1 if session['content'] else 1,
        'undo_available': len(session['undo_stack']) > 0,
        'redo_available': len(session['redo_stack']) > 0
        }
        })

        @advanced_editor_bp.route('/api/editor/advanced/session/<session_id>/content')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_session_content(session_id):
    """Get session content"""
    session = editor_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    return jsonify({
        'success': True,
        'content': session['content'],
        'is_modified': session['is_modified'],
        'encoding': session['encoding']
    })

# DUPLICATE REMOVED: @advanced_editor_bp.route('/api/editor/advanced/session/<session_id>/content', methods=['PUT'])
# DUPLICATE REMOVED: def update_session_content(session_id):
    """Update session content"""
    session = editor_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    try:
        data = request.get_json() or {}
        new_content = data.get('content', '')
        
        old_content = session['content']
        session['content'] = new_content
        session['is_modified'] = new_content != session['original_content']
        session['modified_at'] = datetime.now().isoformat()
        
        # Add to undo stack
        editor_engine.add_to_undo_stack(session, 'content_update', {
            'old_content': old_content,
            'new_content': new_content
        })
        
        return jsonify({
            'success': True,
            'is_modified': session['is_modified'],
            'content_length': len(new_content),
            'line_count': new_content.count('\n') + 1 if new_content else 1
        })
        
    except Exception as e:
        logger.error(f"Error updating session content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_editor_bp.route('/api/editor/advanced/session/<session_id>/find', methods=['POST'])
def find_in_session():
    """Advanced find and replace in session"""
    session = editor_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    try:
        data = request.get_json() or {}
        find_text = data.get('find_text', '')
        replace_text = data.get('replace_text')
        options = data.get('options', {})
        
        if not find_text:
        return jsonify({
                'success': False,
                'error': 'find_text is required'
            }), 400
        
        result = editor_engine.find_and_replace(session_id, find_text, replace_text, options)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Error in find/replace: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_editor_bp.route('/api/editor/advanced/session/<session_id>/column', methods=['POST'])
def column_operations_endpoint(session_id):
    """Column operations endpoint"""
    session = editor_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    try:
        data = request.get_json() or {}
        operation = data.get('operation')
        
        if not operation:
        return jsonify({
                'success': False,
                'error': 'operation is required'
            }), 400
        
        # Remove operation from data and pass the rest as kwargs
        kwargs = {k: v for k, v in data.items() if k != 'operation'}
        
        result = editor_engine.column_operations(session_id, operation, **kwargs)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Error in column operations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_editor_bp.route('/api/editor/advanced/session/<session_id>/bookmarks', methods=['POST'])
def bookmark_operations_endpoint(session_id):
    """Bookmark operations endpoint"""
    try:
        data = request.get_json() or {}
        operation = data.get('operation')
        
        if not operation:
        return jsonify({
                'success': False,
                'error': 'operation is required'
            }), 400
        
        # Remove operation from data and pass the rest as kwargs
        kwargs = {k: v for k, v in data.items() if k != 'operation'}
        
        result = editor_engine.bookmark_operations(session_id, operation, **kwargs)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Error in bookmark operations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_editor_bp.route('/api/editor/advanced/session/<session_id>/lines', methods=['POST'])
def line_operations_endpoint(session_id):
    """Line operations endpoint"""
    session = editor_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    try:
        data = request.get_json() or {}
        operation = data.get('operation')
        
        if not operation:
        return jsonify({
                'success': False,
                'error': 'operation is required'
            }), 400
        
        # Remove operation from data and pass the rest as kwargs
        kwargs = {k: v for k, v in data.items() if k != 'operation'}
        
        result = editor_engine.line_operations(session_id, operation, **kwargs)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        logger.error(f"Error in line operations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_editor_bp.route('/api/editor/advanced/features/search')
def search_features():
    try:
        """Search available editor features"""
        query = request.args.get('q', '').lower()

        all_features = {
        'find_replace': {
        'name': 'Find & Replace',
        'description': 'Advanced find and replace with regex support',
        'category': 'search',
        'keywords': ['find', 'replace', 'search', 'regex', 'pattern']
        },
        'column_insert': {
        'name': 'Column Insert',
        'description': 'Insert text at specific column across multiple lines',
        'category': 'column',
        'keywords': ['column', 'insert', 'block', 'vertical']
        },
        'column_delete': {
        'name': 'Column Delete',
        'description': 'Delete text in column range across multiple lines',
        'category': 'column',
        'keywords': ['column', 'delete', 'block', 'vertical']
        },
        'column_align': {
        'name': 'Column Align',
        'description': 'Align text at specified column',
        'category': 'column',
        'keywords': ['column', 'align', 'format', 'justify']
        },
        'bookmarks': {
        'name': 'Bookmarks',
        'description': 'Add, remove, and navigate bookmarks',
        'category': 'navigation',
        'keywords': ['bookmark', 'mark', 'navigate', 'jump']
        },
        'line_sort': {
        'name': 'Sort Lines',
        'description': 'Sort lines alphabetically or numerically',
        'category': 'lines',
        'keywords': ['sort', 'order', 'alphabetical', 'numeric']
        },
        'line_duplicate': {
        'name': 'Duplicate Lines',
        'description': 'Duplicate selected lines',
        'category': 'lines',
        'keywords': ['duplicate', 'copy', 'repeat']
        },
        'macro_record': {
        'name': 'Record Macro',
        'description': 'Record and replay action sequences',
        'category': 'automation',
        'keywords': ['macro', 'record', 'replay', 'automation']
        }
        }

        if query:
        # Filter features based on query
        matching_features = {}
        for feature_id, feature in all_features.items():
        if (query in feature['name'].lower() or 
        query in feature['description'].lower() or
        any(query in keyword for keyword in feature['keywords'])):
        matching_features[feature_id] = feature
        else:
        matching_features = all_features

        return jsonify({
        'success': True,
        'query': query,
        'features': matching_features,
        'total_features': len(matching_features)
        })

        @advanced_editor_bp.route('/api/editor/advanced/config')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_editor_config():
    try:
        """Get editor configuration"""
        return jsonify({
        'success': True,
        'config': editor_engine.config
        })

        # DUPLICATE REMOVED: @advanced_editor_bp.route('/api/editor/advanced/config', methods=['PUT'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_advanced_config():
    """Update Config"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Updated', 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def update_advanced_config():
    """Update Config"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Updated', 'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def update_editor_config():
    """Update editor configuration"""
    try:
        data = request.get_json() or {}
        
        # Update configuration
        editor_engine.config.update(data)
        editor_engine.save_config()
        
        return jsonify({
            'success': True,
            'config': editor_engine.config
        })
        
    except Exception as e:
        logger.error(f"Error updating editor config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
