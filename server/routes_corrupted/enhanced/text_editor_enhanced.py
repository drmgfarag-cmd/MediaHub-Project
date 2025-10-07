"""
Enhanced Text Editor with Notepad++ and Text Mechanic parity
Provides advanced text editing capabilities with column mode, multi-cursor, and text manipulation
"""

import os
import re
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint('text_editor_enhanced', __name__)

class TextMechanicEngine:
    """Text Mechanic functionality for advanced text manipulation"""
    
    def __init__(self):
        self.operations = {
            # Line operations
            'add_line_numbers': self.add_line_numbers,
            'remove_line_numbers': self.remove_line_numbers,
            'add_line_prefix': self.add_line_prefix,
            'add_line_suffix': self.add_line_suffix,
            'remove_empty_lines': self.remove_empty_lines,
            'remove_duplicate_lines': self.remove_duplicate_lines,
            'sort_lines': self.sort_lines,
            'reverse_lines': self.reverse_lines,
            'shuffle_lines': self.shuffle_lines,
            
            # Case operations
            'uppercase': self.uppercase,
            'lowercase': self.lowercase,
            'title_case': self.title_case,
            'sentence_case': self.sentence_case,
            'camel_case': self.camel_case,
            'snake_case': self.snake_case,
            'kebab_case': self.kebab_case,
            
            # Whitespace operations
            'trim_whitespace': self.trim_whitespace,
            'normalize_whitespace': self.normalize_whitespace,
            'tabs_to_spaces': self.tabs_to_spaces,
            'spaces_to_tabs': self.spaces_to_tabs,
            
            # Text generation
            'generate_lorem_ipsum': self.generate_lorem_ipsum,
            'generate_numbers': self.generate_numbers,
            'generate_alphabet': self.generate_alphabet,
            
            # Advanced operations
            'extract_emails': self.extract_emails,
            'extract_urls': self.extract_urls,
            'extract_numbers': self.extract_numbers,
            'word_count': self.word_count,
            'character_count': self.character_count,
        }
    
    def execute_operation(self, operation: str, text: str, **kwargs) -> Dict[str, Any]:
        """Execute a text manipulation operation"""
        if operation not in self.operations:
            return {'success': False, 'error': f'Unknown operation: {operation}'}
        
        try:
            result = self.operations[operation](text, **kwargs)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_line_numbers(self, text: str, start: int = 1, **kwargs) -> str:
        """Add line numbers to text"""
        lines = text.split('\n')
        numbered_lines = []
        for i, line in enumerate(lines):
            numbered_lines.append(f"{start + i:4d}: {line}")
        return '\n'.join(numbered_lines)
    
    def remove_line_numbers(self, text: str, **kwargs) -> str:
        """Remove line numbers from text"""
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove common line number patterns
            cleaned = re.sub(r'^\s*\d+[:.\s]+', '', line)
            cleaned_lines.append(cleaned)
        return '\n'.join(cleaned_lines)
    
    def add_line_prefix(self, text: str, prefix: str = '', **kwargs) -> str:
        """Add prefix to each line"""
        lines = text.split('\n')
        return '\n'.join(f"{prefix}{line}" for line in lines)
    
    def add_line_suffix(self, text: str, suffix: str = '', **kwargs) -> str:
        """Add suffix to each line"""
        lines = text.split('\n')
        return '\n'.join(f"{line}{suffix}" for line in lines)
    
    def remove_empty_lines(self, text: str, **kwargs) -> str:
        """Remove empty lines"""
        lines = text.split('\n')
        return '\n'.join(line for line in lines if line.strip())
    
    def remove_duplicate_lines(self, text: str, **kwargs) -> str:
        """Remove duplicate lines while preserving order"""
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            if line not in seen:
                seen.add(line)
                unique_lines.append(line)
        return '\n'.join(unique_lines)
    
    def sort_lines(self, text: str, reverse: bool = False, **kwargs) -> str:
        """Sort lines alphabetically"""
        lines = text.split('\n')
        return '\n'.join(sorted(lines, reverse=reverse))
    
    def reverse_lines(self, text: str, **kwargs) -> str:
        """Reverse line order"""
        lines = text.split('\n')
        return '\n'.join(reversed(lines))
    
    def shuffle_lines(self, text: str, **kwargs) -> str:
        """Shuffle lines randomly"""
        import random
        lines = text.split('\n')
        random.shuffle(lines)
        return '\n'.join(lines)
    
    def uppercase(self, text: str, **kwargs) -> str:
        """Convert to uppercase"""
        return text.upper()
    
    def lowercase(self, text: str, **kwargs) -> str:
        """Convert to lowercase"""
        return text.lower()
    
    def title_case(self, text: str, **kwargs) -> str:
        """Convert to title case"""
        return text.title()
    
    def sentence_case(self, text: str, **kwargs) -> str:
        """Convert to sentence case"""
        sentences = re.split(r'([.!?]+)', text)
        result = []
        for i, sentence in enumerate(sentences):
            if i % 2 == 0 and sentence.strip():  # Actual sentence, not punctuation
                sentence = sentence.strip().lower()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
            result.append(sentence)
        return ''.join(result)
    
    def camel_case(self, text: str, **kwargs) -> str:
        """Convert to camelCase"""
        words = re.findall(r'\w+', text)
        if not words:
            return text
        return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    
    def snake_case(self, text: str, **kwargs) -> str:
        """Convert to snake_case"""
        # Replace spaces and special characters with underscores
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text)
        return text.lower()
    
    def kebab_case(self, text: str, **kwargs) -> str:
        """Convert to kebab-case"""
        # Replace spaces and special characters with hyphens
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '-', text)
        return text.lower()
    
    def trim_whitespace(self, text: str, **kwargs) -> str:
        """Trim whitespace from each line"""
        lines = text.split('\n')
        return '\n'.join(line.strip() for line in lines)
    
    def normalize_whitespace(self, text: str, **kwargs) -> str:
        """Normalize whitespace (multiple spaces to single)"""
        return re.sub(r'\s+', ' ', text).strip()
    
    def tabs_to_spaces(self, text: str, tab_size: int = 4, **kwargs) -> str:
        """Convert tabs to spaces"""
        return text.expandtabs(tab_size)
    
    def spaces_to_tabs(self, text: str, tab_size: int = 4, **kwargs) -> str:
        """Convert spaces to tabs"""
        lines = text.split('\n')
        result_lines = []
        for line in lines:
            # Convert leading spaces to tabs
            leading_spaces = len(line) - len(line.lstrip(' '))
            if leading_spaces > 0:
                tabs = leading_spaces // tab_size
                remaining_spaces = leading_spaces % tab_size
                line = '\t' * tabs + ' ' * remaining_spaces + line.lstrip(' ')
            result_lines.append(line)
        return '\n'.join(result_lines)
    
    def generate_lorem_ipsum(self, text: str, words: int = 100, **kwargs) -> str:
        """Generate Lorem Ipsum text"""
        lorem_words = [
            'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
            'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
            'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
            'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
            'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
            'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
            'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
            'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum'
        ]
        
        import random
        result_words = []
        for i in range(words):
            result_words.append(lorem_words[i % len(lorem_words)])
        
        # Capitalize first word and add periods
        result = ' '.join(result_words)
        result = result[0].upper() + result[1:]
        
        # Add periods every 10-20 words
        words_list = result.split()
        final_words = []
        for i, word in enumerate(words_list):
            final_words.append(word)
            if (i + 1) % random.randint(10, 20) == 0 and i < len(words_list) - 1:
                final_words[-1] += '.'
                if i + 1 < len(words_list):
                    final_words.append(words_list[i + 1].capitalize())
                    i += 1
        
        return ' '.join(final_words) + '.'
    
    def generate_numbers(self, text: str, start: int = 1, end: int = 100, **kwargs) -> str:
        """Generate sequence of numbers"""
        return '\n'.join(str(i) for i in range(start, end + 1))
    
    def generate_alphabet(self, text: str, uppercase: bool = False, **kwargs) -> str:
        """Generate alphabet"""
        import string
        alphabet = string.ascii_uppercase if uppercase else string.ascii_lowercase
        return '\n'.join(alphabet)
    
    def extract_emails(self, text: str, **kwargs) -> str:
        """Extract email addresses"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return '\n'.join(emails)
    
    def extract_urls(self, text: str, **kwargs) -> str:
        """Extract URLs"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        return '\n'.join(urls)
    
    def extract_numbers(self, text: str, **kwargs) -> str:
        """Extract numbers"""
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        return '\n'.join(numbers)
    
    def word_count(self, text: str, **kwargs) -> str:
        """Count words"""
        words = len(re.findall(r'\b\w+\b', text))
        return f"Word count: {words}"
    
    def character_count(self, text: str, **kwargs) -> str:
        """Count characters"""
        chars = len(text)
        chars_no_spaces = len(text.replace(' ', ''))
        return f"Characters: {chars} (without spaces: {chars_no_spaces})"

class AdvancedFindReplace:
    """Advanced find and replace with regex and bookmarks"""
    
    def __init__(self):
        self.bookmarks = {}
        self.search_history = []
        self.replace_history = []
    
    def find_all(self, text: str, pattern: str, regex: bool = False, 
                case_sensitive: bool = False, whole_word: bool = False) -> List[Dict[str, Any]]:
        """Find all occurrences of pattern"""
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            
            if regex:
                search_pattern = pattern
            else:
                search_pattern = re.escape(pattern)
                
            if whole_word:
                search_pattern = r'\b' + search_pattern + r'\b'
            
            matches = []
            for match in re.finditer(search_pattern, text, flags):
                line_start = text.rfind('\n', 0, match.start()) + 1
                line_end = text.find('\n', match.end())
                if line_end == -1:
                    line_end = len(text)
                
                line_number = text[:match.start()].count('\n') + 1
                column = match.start() - line_start + 1
                
                matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'line': line_number,
                    'column': column,
                    'text': match.group(),
                    'context': text[line_start:line_end]
                })
            
            # Add to search history
            if pattern not in self.search_history:
                self.search_history.append(pattern)
                if len(self.search_history) > 50:
                    self.search_history.pop(0)
            
            return matches
        
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def replace_all(self, text: str, pattern: str, replacement: str, 
                   regex: bool = False, case_sensitive: bool = False, 
                   whole_word: bool = False) -> Tuple[str, int]:
        """Replace all occurrences of pattern"""
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            
            if regex:
                search_pattern = pattern
            else:
                search_pattern = re.escape(pattern)
                
            if whole_word:
                search_pattern = r'\b' + search_pattern + r'\b'
            
            new_text, count = re.subn(search_pattern, replacement, text, flags=flags)
            
            # Add to replace history
            if replacement not in self.replace_history:
                self.replace_history.append(replacement)
                if len(self.replace_history) > 50:
                    self.replace_history.pop(0)
            
            return new_text, count
        
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def add_bookmark(self, name: str, line: int, column: int = 0):
        """Add a bookmark"""
        self.bookmarks[name] = {'line': line, 'column': column}
    
    def remove_bookmark(self, name: str):
        """Remove a bookmark"""
        if name in self.bookmarks:
            del self.bookmarks[name]
    
    def get_bookmarks(self) -> Dict[str, Dict[str, int]]:
        """Get all bookmarks"""
        return self.bookmarks.copy()

class EditorSessionManager:
    """Manages editor sessions with multi-tab support"""
    
    def __init__(self, db_connection, db_lock):
        self.db_connection = db_connection
        self.db_lock = db_lock
        self.active_sessions = {}
    
    def create_session(self, session_id: str = None) -> str:
        """Create a new editor session"""
        if not session_id:
            session_id = f"session_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        
        session_data = {
            'session_id': session_id,
            'files': {},
            'cursor_positions': {},
            'bookmarks': {},
            'find_history': [],
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat()
        }
        
        self.active_sessions[session_id] = session_data
        self.save_session(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_accessed'] = datetime.now().isoformat()
            return self.active_sessions[session_id]
        
        # Try to load from database
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT files, cursor_positions, bookmarks, find_history, created_at
                    FROM editor_sessions WHERE session_id = ?
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    session_data = {
                        'session_id': session_id,
                        'files': json.loads(row[0]) if row[0] else {},
                        'cursor_positions': json.loads(row[1]) if row[1] else {},
                        'bookmarks': json.loads(row[2]) if row[2] else {},
                        'find_history': json.loads(row[3]) if row[3] else [],
                        'created_at': row[4],
                        'last_accessed': datetime.now().isoformat()
                    }
                    
                    self.active_sessions[session_id] = session_data
                    return session_data
        
        except Exception as e:
            current_app.logger.error(f"Error loading session {session_id}: {e}")
        
        return None
    
    def save_session(self, session_id: str):
        """Save session to database"""
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO editor_sessions
                    (session_id, files, cursor_positions, bookmarks, find_history, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    session_id,
                    json.dumps(session['files']),
                    json.dumps(session['cursor_positions']),
                    json.dumps(session['bookmarks']),
                    json.dumps(session['find_history'])
                ))
                self.db_connection.commit()
        
        except Exception as e:
            current_app.logger.error(f"Error saving session {session_id}: {e}")
    
    def open_file(self, session_id: str, file_path: str) -> Dict[str, Any]:
        """Open a file in the session"""
        session = self.get_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            # Security check
            security_manager = current_app.config['security_manager']
            if not security_manager.validate_path(file_path):
                return {'success': False, 'error': 'Invalid file path'}
            
            path = Path(file_path)
            if not path.exists():
                # Create new file
                content = ''
                encoding = 'utf-8'
            else:
                # Read existing file
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    encoding = 'utf-8'
                except UnicodeDecodeError:
                    # Try other encodings
                    for enc in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            with open(path, 'r', encoding=enc) as f:
                                content = f.read()
                            encoding = enc
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        return {'success': False, 'error': 'Unable to decode file'}
            
            file_info = {
                'path': str(path),
                'name': path.name,
                'content': content,
                'encoding': encoding,
                'size': len(content),
                'modified': path.stat().st_mtime if path.exists() else time.time(),
                'readonly': not os.access(path.parent, os.W_OK) if path.exists() else False
            }
            
            session['files'][file_path] = file_info
            session['cursor_positions'][file_path] = {'line': 1, 'column': 1}
            
            self.save_session(session_id)
            
            return {
                'success': True,
                'file': file_info
            }
        
        except Exception as e:
            current_app.logger.error(f"Error opening file {file_path}: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_file(self, session_id: str, file_path: str, content: str) -> Dict[str, Any]:
        """Save file content"""
        session = self.get_session(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            # Security check
            security_manager = current_app.config['security_manager']
            if not security_manager.validate_path(file_path):
                return {'success': False, 'error': 'Invalid file path'}
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine encoding
            encoding = 'utf-8'
            if file_path in session['files']:
                encoding = session['files'][file_path].get('encoding', 'utf-8')
            
            # Save file
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Update session
            if file_path in session['files']:
                session['files'][file_path]['content'] = content
                session['files'][file_path]['size'] = len(content)
                session['files'][file_path]['modified'] = time.time()
            
            self.save_session(session_id)
            
            return {
                'success': True,
                'message': f'File saved: {path.name}',
                'size': len(content)
            }
        
        except Exception as e:
            current_app.logger.error(f"Error saving file {file_path}: {e}")
            return {'success': False, 'error': str(e)}

# Global instances
text_mechanic = TextMechanicEngine()
find_replace = AdvancedFindReplace()

@bp.route('/sessions/create', methods=['POST'])
def create_session():
    """Create a new editor session"""
    try:
        db_connection = current_app.config['db_connection']
        db_lock = current_app.config['db_lock']
        
        session_manager = EditorSessionManager(db_connection, db_lock)
        session_id = session_manager.create_session()
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
    
    except Exception as e:
        current_app.logger.error(f"Create session error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/sessions/<session_id>/files/open', methods=['POST'])
def open_file(session_id):
    """Open a file in the editor"""
    try:
        data = request.json
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'No file path provided'})
        
        db_connection = current_app.config['db_connection']
        db_lock = current_app.config['db_lock']
        
        session_manager = EditorSessionManager(db_connection, db_lock)
        result = session_manager.open_file(session_id, file_path)
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Open file error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/sessions/<session_id>/files/save', methods=['POST'])
def save_file(session_id):
    """Save file content"""
    try:
        data = request.json
        file_path = data.get('file_path')
        content = data.get('content', '')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'No file path provided'})
        
        db_connection = current_app.config['db_connection']
        db_lock = current_app.config['db_lock']
        
        session_manager = EditorSessionManager(db_connection, db_lock)
        result = session_manager.save_file(session_id, file_path, content)
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Save file error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/text-mechanic/operations')
def list_operations():
    """List available text manipulation operations"""
    try:
        operations = {}
        for op_name, op_func in text_mechanic.operations.items():
            # Get operation description from docstring
            description = op_func.__doc__ or op_name.replace('_', ' ').title()
            operations[op_name] = {
                'name': op_name.replace('_', ' ').title(),
                'description': description
            }
        
        return jsonify({
            'success': True,
            'operations': operations
        })
    
    except Exception as e:
        current_app.logger.error(f"List operations error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/text-mechanic/execute', methods=['POST'])
def execute_operation():
    """Execute a text manipulation operation"""
    try:
        data = request.json
        operation = data.get('operation')
        text = data.get('text', '')
        params = data.get('params', {})
        
        if not operation:
            return jsonify({'success': False, 'error': 'No operation specified'})
        
        result = text_mechanic.execute_operation(operation, text, **params)
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Execute operation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/find-replace/find', methods=['POST'])
def find_text():
    """Find text with advanced options"""
    try:
        data = request.json
        text = data.get('text', '')
        pattern = data.get('pattern', '')
        regex = data.get('regex', False)
        case_sensitive = data.get('case_sensitive', False)
        whole_word = data.get('whole_word', False)
        
        if not pattern:
            return jsonify({'success': False, 'error': 'No search pattern provided'})
        
        matches = find_replace.find_all(text, pattern, regex, case_sensitive, whole_word)
        
        return jsonify({
            'success': True,
            'matches': matches,
            'count': len(matches)
        })
    
    except Exception as e:
        current_app.logger.error(f"Find text error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/find-replace/replace', methods=['POST'])
def replace_text():
    """Replace text with advanced options"""
    try:
        data = request.json
        text = data.get('text', '')
        pattern = data.get('pattern', '')
        replacement = data.get('replacement', '')
        regex = data.get('regex', False)
        case_sensitive = data.get('case_sensitive', False)
        whole_word = data.get('whole_word', False)
        
        if not pattern:
            return jsonify({'success': False, 'error': 'No search pattern provided'})
        
        new_text, count = find_replace.replace_all(
            text, pattern, replacement, regex, case_sensitive, whole_word
        )
        
        return jsonify({
            'success': True,
            'text': new_text,
            'replacements': count
        })
    
    except Exception as e:
        current_app.logger.error(f"Replace text error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/bookmarks/<session_id>/add', methods=['POST'])
def add_bookmark(session_id):
    """Add a bookmark"""
    try:
        data = request.json
        name = data.get('name')
        line = data.get('line', 1)
        column = data.get('column', 0)
        
        if not name:
            return jsonify({'success': False, 'error': 'No bookmark name provided'})
        
        find_replace.add_bookmark(name, line, column)
        
        return jsonify({
            'success': True,
            'message': f'Bookmark "{name}" added'
        })
    
    except Exception as e:
        current_app.logger.error(f"Add bookmark error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/bookmarks/<session_id>/list')
def list_bookmarks(session_id):
    """List all bookmarks"""
    try:
        bookmarks = find_replace.get_bookmarks()
        
        return jsonify({
            'success': True,
            'bookmarks': bookmarks
        })
    
    except Exception as e:
        current_app.logger.error(f"List bookmarks error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/history/search')
def get_search_history():
    """Get search history"""
    try:
        return jsonify({
            'success': True,
            'search_history': find_replace.search_history,
            'replace_history': find_replace.replace_history
        })
    
    except Exception as e:
        current_app.logger.error(f"Get search history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
