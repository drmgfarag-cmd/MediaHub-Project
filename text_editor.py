#!/usr/bin/env python3
"""
Advanced Text Editor - MediaHub Ultimate
Notepad++ parity with Monaco Editor integration
"""

import sys
import os
import json
import re
import threading
import time
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QStatusBar, QToolBar, QFileDialog,
    QMessageBox, QInputDialog, QDialog, QTextEdit, QLineEdit,
    QPushButton, QLabel, QComboBox, QCheckBox, QSpinBox,
    QSplitter, QDockWidget, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QGridLayout, QGroupBox,
    QProgressBar, QSlider, QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QUrl, QTimer, QThread, pyqtSignal, QSettings,
    QSize, QPoint, QRect, QStandardPaths,
    QEventLoop, QObject, pyqtSlot
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QKeySequence, QAction, QTextCursor,
    QTextDocument, QSyntaxHighlighter, QTextCharFormat,
    QColor, QPalette, QFontMetrics
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# Enhanced features implementation
class MacroRecorder:
    """Macro recording and playback functionality"""
    
    def __init__(self):
        self.recording = False
        self.current_macro = []
        self.macros = {}  # name -> commands list
        
    def start_recording(self, name="Macro"):
        """Start recording a new macro"""
        self.recording = True
        self.current_macro = []
        self.macro_name = name
        
    def stop_recording(self):
        """Stop recording and save macro"""
        if self.recording:
            self.recording = False
            self.macros[self.macro_name] = self.current_macro.copy()
            return self.current_macro.copy()
        return []
        
    def record_command(self, command, parameters=None):
        """Record a command during macro recording"""
        if self.recording:
            self.current_macro.append({
                'command': command,
                'parameters': parameters or {},
                'timestamp': time.time()
            })
            
    def play_macro(self, name, editor_instance):
        """Play back a recorded macro"""
        if name in self.macros:
            commands = self.macros[name]
            for cmd in commands:
                self._execute_command(cmd, editor_instance)
                
    def _execute_command(self, cmd, editor_instance):
        """Execute a single macro command"""
        command = cmd['command']
        params = cmd['parameters']
        
        if command == 'insert_text':
            editor_instance.page().runJavaScript(
                f"window.monacoEditor.insertText({json.dumps(params.get('text', ''))});"
            )
        elif command == 'move_cursor':
            line = params.get('line', 1)
            col = params.get('column', 1)
            editor_instance.page().runJavaScript(
                f"window.monacoEditor.setCursorPosition({line}, {col});"
            )
        elif command == 'find':
            editor_instance.find()
        elif command == 'replace':
            editor_instance.replace()
        # Add more commands as needed

class FileSearcher:
    """File search functionality"""
    
    def __init__(self):
        self.search_thread = None
        
    def search_in_files(self, pattern, directory, file_filter="*.*", 
                       case_sensitive=False, whole_word=False, regex=False,
                       include_subdirs=True, callback=None):
        """Search for pattern in files"""
        import glob
        import fnmatch
        
        results = []
        search_pattern = pattern
        
        if not regex:
            search_pattern = re.escape(pattern)
        if whole_word:
            search_pattern = r'\b' + search_pattern + r'\b'
            
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            compiled_pattern = re.compile(search_pattern, flags)
        except re.error as e:
            if callback:
                callback(None, f"Invalid regex pattern: {e}")
            return []
            
        # Get files to search
        if include_subdirs:
            search_path = os.path.join(directory, "**", file_filter)
            files = glob.glob(search_path, recursive=True)
        else:
            search_path = os.path.join(directory, file_filter)
            files = glob.glob(search_path)
            
        for file_path in files:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, 1):
                            matches = list(compiled_pattern.finditer(line))
                            for match in matches:
                                results.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'column': match.start() + 1,
                                    'match': match.group(),
                                    'context': line.strip()
                                })
                except (UnicodeDecodeError, PermissionError):
                    continue
                    
        if callback:
            callback(results, None)
        return results

class BookmarkManager:
    """Bookmark management"""
    
    def __init__(self):
        self.bookmarks = {}  # file_path -> {line_number: description}
        
    def add_bookmark(self, file_path, line_number, description=""):
        """Add a bookmark"""
        if file_path not in self.bookmarks:
            self.bookmarks[file_path] = {}
        self.bookmarks[file_path][line_number] = description
        
    def remove_bookmark(self, file_path, line_number):
        """Remove a bookmark"""
        if file_path in self.bookmarks and line_number in self.bookmarks[file_path]:
            del self.bookmarks[file_path][line_number]
            
    def toggle_bookmark(self, file_path, line_number, description=""):
        """Toggle bookmark at line"""
        if self.has_bookmark(file_path, line_number):
            self.remove_bookmark(file_path, line_number)
            return False
        else:
            self.add_bookmark(file_path, line_number, description)
            return True
            
    def has_bookmark(self, file_path, line_number):
        """Check if bookmark exists"""
        return (file_path in self.bookmarks and 
                line_number in self.bookmarks[file_path])
                
    def get_next_bookmark(self, file_path, current_line):
        """Get next bookmark after current line"""
        if file_path not in self.bookmarks:
            return None
            
        bookmarks = sorted(self.bookmarks[file_path].keys())
        for line in bookmarks:
            if line > current_line:
                return type('Bookmark', (), {
                    'line_number': line,
                    'description': self.bookmarks[file_path][line]
                })()
        return None
        
    def get_previous_bookmark(self, file_path, current_line):
        """Get previous bookmark before current line"""
        if file_path not in self.bookmarks:
            return None
            
        bookmarks = sorted(self.bookmarks[file_path].keys(), reverse=True)
        for line in bookmarks:
            if line < current_line:
                return type('Bookmark', (), {
                    'line_number': line,
                    'description': self.bookmarks[file_path][line]
                })()
        return None

# Utility functions
def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def detect_line_endings(content):
    """Detect line ending type"""
    if '\r\n' in content:
        return 'CRLF'
    elif '\r' in content:
        return 'CR'
    else:
        return 'LF'

def normalize_line_endings(content, target='LF'):
    """Normalize line endings"""
    if target == 'LF':
        return content.replace('\r\n', '\n').replace('\r', '\n')
    elif target == 'CRLF':
        return content.replace('\r\n', '\n').replace('\r', '\n').replace('\n', '\r\n')
    elif target == 'CR':
        return content.replace('\r\n', '\n').replace('\n', '\r')
    return content


class MonacoEditorBridge(QObject):
    """Bridge between Python and Monaco Editor JavaScript"""
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.callbacks = {}
        
    def register_callback(self, name, callback):
        """Register a Python callback for JavaScript"""
        self.callbacks[name] = callback
        
    @pyqtSlot(str, result=str)
    def call_python(self, method, *args):
        """Called from JavaScript to execute Python code"""
        try:
            if method in self.callbacks:
                result = self.callbacks[method](*args)
                return str(result) if result is not None else ""
        except Exception as e:
            print(f"Bridge error: {e}")
        return ""


class MonacoEditor(QWebEngineView):
    """Monaco Editor embedded in PyQt WebEngine"""
    
    # Signals
    content_changed = pyqtSignal(str)
    cursor_changed = pyqtSignal(int, int)  # line, column
    selection_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.bridge = MonacoEditorBridge(self)
        self.setup_monaco()
        
    def setup_monaco(self):
        """Setup Monaco Editor in WebEngine"""
        # Create the HTML content with Monaco Editor
        html_content = self.create_monaco_html()
        
        # Create a temporary HTML file
        html_file = Path("static/monaco-editor/editor.html")
        html_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Load the HTML file
        self.load(QUrl.fromLocalFile(str(html_file.absolute())))
        
        # Setup communication channel
        self.channel = QWebChannel()
        self.page().setWebChannel(self.channel)
        self.channel.registerObject("bridge", self.bridge)
        
        # Setup callbacks
        self.bridge.register_callback('content_changed', self._on_content_changed)
        self.bridge.register_callback('cursor_changed', self._on_cursor_changed)
        self.bridge.register_callback('selection_changed', self._on_selection_changed)
        
    def create_monaco_html(self):
        """Create HTML content with Monaco Editor"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monaco Editor</title>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}
        #container {{
            width: 100%;
            height: 100vh;
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    
    <script src="./min/vs/loader.js"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        let editor;
        let bridge;
        
        // Initialize WebChannel communication
        new QWebChannel(qt.webChannelTransport, function(channel) {{
            bridge = channel.objects.bridge;
            initializeMonaco();
        }});
        
        function initializeMonaco() {{
            require.config({{
                paths: {{
                    'vs': './min/vs'
                }}
            }});
            
            require(['vs/editor/editor.main'], function() {{
                // Configure Monaco Editor
                monaco.editor.defineTheme('dark-theme', {{
                    base: 'vs-dark',
                    inherit: true,
                    rules: [
                        {{ token: 'comment', foreground: '6A9955' }},
                        {{ token: 'keyword', foreground: '569CD6' }},
                        {{ token: 'string', foreground: 'CE9178' }},
                        {{ token: 'number', foreground: 'B5CEA8' }}
                    ],
                    colors: {{
                        'editor.background': '#1e1e1e',
                        'editor.foreground': '#d4d4d4',
                        'editor.lineHighlightBackground': '#2d2d30',
                        'editor.selectionBackground': '#264f78',
                        'editorCursor.foreground': '#ffffff'
                    }}
                }});
                
                // Create the editor
                editor = monaco.editor.create(document.getElementById('container'), {{
                    value: '',
                    language: 'plaintext',
                    theme: 'dark-theme',
                    fontSize: 14,
                    fontFamily: 'Consolas, Monaco, Courier New, monospace',
                    lineNumbers: 'on',
                    minimap: {{ enabled: true }},
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    wordWrap: 'off',
                    folding: true,
                    foldingStrategy: 'auto',
                    showFoldingControls: 'always',
                    unfoldOnClickAfterEndOfLine: false,
                    tabSize: 4,
                    insertSpaces: true,
                    detectIndentation: true,
                    trimAutoWhitespace: true,
                    acceptSuggestionOnCommitCharacter: true,
                    acceptSuggestionOnEnter: 'on',
                    accessibilitySupport: 'auto',
                    autoIndent: 'advanced',
                    contextmenu: true,
                    copyWithSyntaxHighlighting: true,
                    cursorBlinking: 'blink',
                    cursorSmoothCaretAnimation: true,
                    cursorStyle: 'line',
                    disableLayerHinting: false,
                    disableMonospaceOptimizations: false,
                    dragAndDrop: true,
                    emptySelectionClipboard: true,
                    extraEditorClassName: '',
                    fastScrollSensitivity: 5,
                    find: {{
                        autoFindInSelection: 'never',
                        seedSearchStringFromSelection: true
                    }},
                    fixedOverflowWidgets: false,
                    hover: {{ enabled: true }},
                    inDiffEditor: false,
                    letterSpacing: 0,
                    lightbulb: {{ enabled: true }},
                    lineDecorationsWidth: 10,
                    lineHeight: 0,
                    lineNumbersMinChars: 5,
                    links: true,
                    mouseWheelScrollSensitivity: 1,
                    mouseWheelZoom: false,
                    multiCursorMergeOverlapping: true,
                    multiCursorModifier: 'alt',
                    overviewRulerBorder: true,
                    overviewRulerLanes: 2,
                    padding: {{ top: 0, bottom: 0 }},
                    parameterHints: {{ enabled: true }},
                    quickSuggestions: true,
                    quickSuggestionsDelay: 500,
                    readOnly: false,
                    renderControlCharacters: false,
                    renderIndentGuides: true,
                    renderLineHighlight: 'line',
                    renderWhitespace: 'selection',
                    revealHorizontalRightPadding: 30,
                    roundedSelection: true,
                    rulers: [],
                    scrollbar: {{
                        vertical: 'auto',
                        horizontal: 'auto',
                        arrowSize: 11,
                        useShadows: true,
                        verticalHasArrows: false,
                        horizontalHasArrows: false,
                        verticalScrollbarSize: 14,
                        horizontalScrollbarSize: 10,
                        verticalSliderSize: 14,
                        horizontalSliderSize: 10
                    }},
                    selectOnLineNumbers: true,
                    selectionClipboard: true,
                    selectionHighlight: true,
                    showUnused: true,
                    smoothScrolling: false,
                    suggestOnTriggerCharacters: true,
                    useTabStops: true,
                    wordSeparators: '`~!@#$%^&*()-=+[{{]}}\\|;:\'\",.<>/?',
                    wordWrap: 'off',
                    wordWrapBreakAfterCharacters: '\t}})]?|&,;',
                    wordWrapBreakBeforeCharacters: '{{([+',
                    wordWrapColumn: 80,
                    wrappingIndent: 'none'
                }});
                
                // Setup event listeners
                editor.onDidChangeModelContent(function(e) {{
                    if (bridge) {{
                        bridge.call_python('content_changed', editor.getValue());
                    }}
                }});
                
                editor.onDidChangeCursorPosition(function(e) {{
                    if (bridge) {{
                        bridge.call_python('cursor_changed', e.position.lineNumber, e.position.column);
                    }}
                }});
                
                editor.onDidChangeCursorSelection(function(e) {{
                    if (bridge) {{
                        const selection = editor.getModel().getValueInRange(e.selection);
                        bridge.call_python('selection_changed', selection);
                    }}
                }});
                
                // Expose editor methods to Python
                window.monacoEditor = {{
                    setValue: function(value) {{
                        editor.setValue(value);
                    }},
                    getValue: function() {{
                        return editor.getValue();
                    }},
                    setLanguage: function(language) {{
                        monaco.editor.setModelLanguage(editor.getModel(), language);
                    }},
                    setTheme: function(theme) {{
                        monaco.editor.setTheme(theme);
                    }},
                    focus: function() {{
                        editor.focus();
                    }},
                    undo: function() {{
                        editor.trigger('keyboard', 'undo');
                    }},
                    redo: function() {{
                        editor.trigger('keyboard', 'redo');
                    }},
                    find: function() {{
                        editor.trigger('keyboard', 'actions.find');
                    }},
                    replace: function() {{
                        editor.trigger('keyboard', 'editor.action.startFindReplaceAction');
                    }},
                    gotoLine: function() {{
                        editor.trigger('keyboard', 'editor.action.gotoLine');
                    }},
                    formatDocument: function() {{
                        editor.trigger('keyboard', 'editor.action.formatDocument');
                    }},
                    toggleWordWrap: function() {{
                        const currentWordWrap = editor.getOption(monaco.editor.EditorOption.wordWrap);
                        editor.updateOptions({{
                            wordWrap: currentWordWrap === 'off' ? 'on' : 'off'
                        }});
                    }},
                    setFontSize: function(size) {{
                        editor.updateOptions({{ fontSize: size }});
                    }},
                    insertText: function(text) {{
                        const selection = editor.getSelection();
                        const id = {{ major: 1, minor: 1 }};
                        const op = {{ identifier: id, range: selection, text: text, forceMoveMarkers: true }};
                        editor.executeEdits('insert-text', [op]);
                    }},
                    setCursorPosition: function(lineNumber, column) {{
                        editor.setPosition({{ lineNumber: lineNumber, column: column }});
                    }},
                    getPosition: function() {{
                        const pos = editor.getPosition();
                        return {{ lineNumber: pos.lineNumber, column: pos.column }};
                    }},
                    addBookmark: function(lineNumber) {{
                        // Add bookmark decoration
                        const decorations = editor.deltaDecorations([], [{{
                            range: new monaco.Range(lineNumber, 1, lineNumber, 1),
                            options: {{
                                isWholeLine: true,
                                className: 'bookmark-line',
                                glyphMarginClassName: 'bookmark-glyph'
                            }}
                        }}]);
                        return decorations[0];
                    }},
                    removeBookmark: function(decorationId) {{
                        editor.deltaDecorations([decorationId], []);
                    }}
                }};
                
                // Custom CSS for bookmarks
                const style = document.createElement('style');
                style.textContent = `
                    .bookmark-line {{
                        background-color: rgba(0, 122, 204, 0.2);
                    }}
                    .bookmark-glyph {{
                        background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgMlYxNEw4IDEwLjVMMTMgMTRWMkgzWiIgZmlsbD0iIzAwN0FDQyIvPgo8L3N2Zz4K') no-repeat center center;
                    }}
                `;
                document.head.appendChild(style);
                
                console.log('Monaco Editor initialized successfully');
            }});
        }}
    </script>
</body>
</html>
        """
    
    def _on_content_changed(self, content):
        """Handle content change from Monaco"""
        self.content_changed.emit(content)
        
    def _on_cursor_changed(self, line, column):
        """Handle cursor position change from Monaco"""
        self.cursor_changed.emit(line, column)
        
    def _on_selection_changed(self, selection):
        """Handle selection change from Monaco"""
        self.selection_changed.emit(selection)
    
    def set_content(self, content):
        """Set editor content"""
        self.page().runJavaScript(f"window.monacoEditor.setValue({json.dumps(content)});")
    
    def get_content(self, callback=None):
        """Get editor content"""
        if callback:
            self.page().runJavaScript("window.monacoEditor.getValue();", callback)
        else:
            # Synchronous version using QEventLoop
            loop = QEventLoop()
            result = []
            
            def handle_result(content):
                result.append(content)
                loop.quit()
            
            self.page().runJavaScript("window.monacoEditor.getValue();", handle_result)
            loop.exec_()
            return result[0] if result else ""
    
    def set_language(self, language):
        """Set syntax highlighting language"""
        # Map common language names to Monaco language IDs
        language_map = {
            'Python': 'python',
            'JavaScript': 'javascript',
            'TypeScript': 'typescript',
            'HTML': 'html',
            'CSS': 'css',
            'JSON': 'json',
            'XML': 'xml',
            'C': 'c',
            'C++': 'cpp',
            'C#': 'csharp',
            'Java': 'java',
            'PHP': 'php',
            'Ruby': 'ruby',
            'Go': 'go',
            'Rust': 'rust',
            'Swift': 'swift',
            'Kotlin': 'kotlin',
            'SQL': 'sql',
            'Shell': 'shell',
            'PowerShell': 'powershell',
            'Batch': 'bat',
            'Dockerfile': 'dockerfile',
            'YAML': 'yaml',
            'TOML': 'toml',
            'Markdown': 'markdown',
            'LaTeX': 'latex',
            'R': 'r',
            'MATLAB': 'matlab',
            'Perl': 'perl',
            'Lua': 'lua',
            'Scala': 'scala',
            'Haskell': 'haskell',
            'Plain Text': 'plaintext'
        }
        
        monaco_lang = language_map.get(language, 'plaintext')
        self.page().runJavaScript(f"window.monacoEditor.setLanguage('{monaco_lang}');")
    
    def undo(self):
        """Undo last action"""
        self.page().runJavaScript("window.monacoEditor.undo();")
    
    def redo(self):
        """Redo last action"""
        self.page().runJavaScript("window.monacoEditor.redo();")
    
    def find(self):
        """Show find dialog"""
        self.page().runJavaScript("window.monacoEditor.find();")
    
    def replace(self):
        """Show replace dialog"""
        self.page().runJavaScript("window.monacoEditor.replace();")
    
    def goto_line(self):
        """Show goto line dialog"""
        self.page().runJavaScript("window.monacoEditor.gotoLine();")
    
    def format_document(self):
        """Format the entire document"""
        self.page().runJavaScript("window.monacoEditor.formatDocument();")
    
    def toggle_word_wrap(self):
        """Toggle word wrap"""
        self.page().runJavaScript("window.monacoEditor.toggleWordWrap();")
    
    def set_font_size(self, size):
        """Set font size"""
        self.page().runJavaScript(f"window.monacoEditor.setFontSize({size});")


class DocumentTab:
    """Represents a document tab with Monaco Editor"""
    
    def __init__(self, parent):
        self.parent = parent
        self.editor = MonacoEditor(parent)
        self.filepath = None
        self.modified = False
        self.encoding = 'utf-8'
        self.language = 'Plain Text'
        self.bookmarks = set()
        
        # Connect signals
        self.editor.content_changed.connect(self._on_content_changed)
        self.editor.cursor_changed.connect(self._on_cursor_changed)
        self.current_line = 1
        self.current_column = 1
        
    def _on_content_changed(self, content):
        """Handle content change"""
        self.modified = True
        self.parent.update_tab_title(self)
        
    def _on_cursor_changed(self, line, column):
        """Handle cursor change"""
        self.current_line = line
        self.current_column = column
        self.parent.update_status_bar(line, column)
        
        # Record cursor movement for macro recording
        if hasattr(self.parent, 'macro_recorder') and self.parent.macro_recorder.recording:
            self.parent.macro_recorder.record_command('move_cursor', {
                'line': line,
                'column': column
            })


class FindReplaceDialog(QDialog):
    """Advanced Find and Replace dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Find and Replace")
        self.setModal(False)
        self.resize(500, 200)
        
        layout = QVBoxLayout()
        
        # Find section
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_input = QLineEdit()
        find_layout.addWidget(self.find_input)
        layout.addLayout(find_layout)
        
        # Replace section
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_input = QLineEdit()
        replace_layout.addWidget(self.replace_input)
        layout.addLayout(replace_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("Case sensitive")
        self.whole_word = QCheckBox("Whole word")
        self.regex = QCheckBox("Regular expression")
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_word)
        options_layout.addWidget(self.regex)
        layout.addLayout(options_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.find_next_btn = QPushButton("Find Next")
        self.find_prev_btn = QPushButton("Find Previous")
        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")
        
        button_layout.addWidget(self.find_next_btn)
        button_layout.addWidget(self.find_prev_btn)
        button_layout.addWidget(self.replace_btn)
        button_layout.addWidget(self.replace_all_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.find_next_btn.clicked.connect(self.find_next)
        self.find_prev_btn.clicked.connect(self.find_previous)
        self.replace_btn.clicked.connect(self.replace)
        self.replace_all_btn.clicked.connect(self.replace_all)
    
    def find_next(self):
        """Find next occurrence"""
        # Implementation would interact with Monaco Editor's find functionality
        pass
    
    def find_previous(self):
        """Find previous occurrence"""
        pass
    
    def replace(self):
        """Replace current selection"""
        pass
    
    def replace_all(self):
        """Replace all occurrences"""
        pass


class FindInFilesDialog(QDialog):
    """Find in Files dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Find in Files")
        self.setModal(False)
        self.resize(600, 400)
        
        layout = QVBoxLayout()
        
        # Search inputs
        search_layout = QGridLayout()
        search_layout.addWidget(QLabel("Find:"), 0, 0)
        self.find_input = QLineEdit()
        search_layout.addWidget(self.find_input, 0, 1)
        
        search_layout.addWidget(QLabel("Files:"), 1, 0)
        self.files_input = QLineEdit("*.*")
        search_layout.addWidget(self.files_input, 1, 1)
        
        search_layout.addWidget(QLabel("Directory:"), 2, 0)
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        dir_browse_btn = QPushButton("Browse")
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(dir_browse_btn)
        search_layout.addLayout(dir_layout, 2, 1)
        
        layout.addLayout(search_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.case_sensitive = QCheckBox("Case sensitive")
        self.whole_word = QCheckBox("Whole word")
        self.regex = QCheckBox("Regular expression")
        self.subdirs = QCheckBox("Include subdirectories")
        self.subdirs.setChecked(True)
        
        options_layout.addWidget(self.case_sensitive)
        options_layout.addWidget(self.whole_word)
        options_layout.addWidget(self.regex)
        options_layout.addWidget(self.subdirs)
        layout.addLayout(options_layout)
        
        # Results
        self.results_list = QTreeWidget()
        self.results_list.setHeaderLabels(["File", "Line", "Match"])
        layout.addWidget(self.results_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.search_btn = QPushButton("Search")
        self.stop_btn = QPushButton("Stop")
        self.close_btn = QPushButton("Close")
        
        button_layout.addWidget(self.search_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        dir_browse_btn.clicked.connect(self.browse_directory)
        self.search_btn.clicked.connect(self.start_search)
        self.close_btn.clicked.connect(self.close)
    
    def browse_directory(self):
        """Browse for directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)
    
    def start_search(self):
        """Start the search"""
        pattern = self.find_input.text()
        if not pattern:
            return
            
        directory = self.dir_input.text() or os.getcwd()
        file_filter = self.files_input.text() or "*.*"
        
        # Clear previous results
        self.results_list.clear()
        
        # Create file searcher and start search
        searcher = FileSearcher()
        results = searcher.search_in_files(
            pattern=pattern,
            directory=directory,
            file_filter=file_filter,
            case_sensitive=self.case_sensitive.isChecked(),
            whole_word=self.whole_word.isChecked(),
            regex=self.regex.isChecked(),
            include_subdirs=self.subdirs.isChecked()
        )
        
        # Populate results
        for result in results:
            item = QTreeWidgetItem([
                os.path.basename(result['file']),
                str(result['line']),
                result['context'][:100] + ('...' if len(result['context']) > 100 else '')
            ])
            item.setData(0, Qt.UserRole, result)
            self.results_list.addTopLevelItem(item)
            
        self.results_list.resizeColumnToContents(0)
        self.results_list.resizeColumnToContents(1)


class AdvancedTextEditor(QMainWindow):
    """Advanced Text Editor with Monaco Editor integration"""
    
    def __init__(self):
        super().__init__()
        self.documents = {}  # doc_id -> DocumentTab
        self.current_doc_id = None
        self.doc_counter = 0
        self.recent_files = []
        self.bookmarks = {}  # file_path -> set of line numbers
        self.macro_recording = False
        self.macro_commands = []
        self.find_dialog = None
        self.find_in_files_dialog = None
        
        # Enhanced features
        self.macro_recorder = MacroRecorder()
        self.file_searcher = FileSearcher()
        self.bookmark_manager = BookmarkManager()
        self.syntax_highlighter = SyntaxHighlighter()
        
        # Settings
        self.settings = QSettings('MediaHub', 'TextEditor')
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_status_bar()
        self.apply_theme()
        
        # Create initial document
        self.new_document()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("MediaHub Ultimate - Advanced Text Editor")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget with tab system
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_document)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        self.setCentralWidget(self.tab_widget)
        
        # File system watcher
        from PyQt6.QtCore import QFileSystemWatcher
        self.file_watcher = QFileSystemWatcher()
        self.file_watcher.fileChanged.connect(self.on_file_changed)
        
        # Current font size for zoom functionality
        self.current_font_size = 14
        
    def setup_menus(self):
        """Setup the menu system"""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu('&File')
        
        # New
        new_action = QAction('&New', self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)
        
        # Open
        open_action = QAction('&Open', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Save
        save_action = QAction('&Save', self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        # Save As
        save_as_action = QAction('Save &As...', self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        # Save All
        save_all_action = QAction('Save A&ll', self)
        save_all_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        save_all_action.triggered.connect(self.save_all_files)
        file_menu.addAction(save_all_action)
        
        file_menu.addSeparator()
        
        # Close
        close_action = QAction('&Close', self)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self.close_current_document)
        file_menu.addAction(close_action)
        
        # Recent Files
        recent_menu = file_menu.addMenu('&Recent Files')
        self.update_recent_files_menu(recent_menu)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu('&Edit')
        
        # Undo
        undo_action = QAction('&Undo', self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        # Redo
        redo_action = QAction('&Redo', self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Find
        find_action = QAction('&Find...', self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        
        # Replace
        replace_action = QAction('&Replace...', self)
        replace_action.setShortcut(QKeySequence.Replace)
        replace_action.triggered.connect(self.show_replace_dialog)
        edit_menu.addAction(replace_action)
        
        # Find in Files
        find_files_action = QAction('Find in &Files...', self)
        find_files_action.setShortcut(QKeySequence('Ctrl+Shift+F'))
        find_files_action.triggered.connect(self.show_find_in_files)
        edit_menu.addAction(find_files_action)
        
        # Go to Line
        goto_action = QAction('&Go to Line...', self)
        goto_action.setShortcut(QKeySequence('Ctrl+G'))
        goto_action.triggered.connect(self.goto_line)
        edit_menu.addAction(goto_action)
        
        edit_menu.addSeparator()
        
        # Bookmarks
        bookmark_menu = edit_menu.addMenu('&Bookmarks')
        
        toggle_bookmark_action = QAction('&Toggle Bookmark', self)
        toggle_bookmark_action.setShortcut(QKeySequence('Ctrl+F2'))
        toggle_bookmark_action.triggered.connect(self.toggle_bookmark)
        bookmark_menu.addAction(toggle_bookmark_action)
        
        next_bookmark_action = QAction('&Next Bookmark', self)
        next_bookmark_action.setShortcut(QKeySequence('F2'))
        next_bookmark_action.triggered.connect(self.next_bookmark)
        bookmark_menu.addAction(next_bookmark_action)
        
        prev_bookmark_action = QAction('&Previous Bookmark', self)
        prev_bookmark_action.setShortcut(QKeySequence('Shift+F2'))
        prev_bookmark_action.triggered.connect(self.previous_bookmark)
        bookmark_menu.addAction(prev_bookmark_action)
        
        # View Menu
        view_menu = menubar.addMenu('&View')
        
        # Toggle Word Wrap
        word_wrap_action = QAction('&Word Wrap', self)
        word_wrap_action.setCheckable(True)
        word_wrap_action.triggered.connect(self.toggle_word_wrap)
        view_menu.addAction(word_wrap_action)
        
        # Zoom
        zoom_menu = view_menu.addMenu('&Zoom')
        
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out)
        zoom_menu.addAction(zoom_out_action)
        
        reset_zoom_action = QAction('&Reset Zoom', self)
        reset_zoom_action.setShortcut(QKeySequence('Ctrl+0'))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        zoom_menu.addAction(reset_zoom_action)
        
        # Macro Menu
        macro_menu = menubar.addMenu('&Macros')
        
        start_recording_action = QAction('&Start Recording', self)
        start_recording_action.setShortcut(QKeySequence('Ctrl+Shift+R'))
        start_recording_action.triggered.connect(self.start_macro_recording)
        macro_menu.addAction(start_recording_action)
        
        stop_recording_action = QAction('St&op Recording', self)
        stop_recording_action.setShortcut(QKeySequence('Ctrl+Shift+S'))
        stop_recording_action.triggered.connect(self.stop_macro_recording)
        macro_menu.addAction(stop_recording_action)
        
        macro_menu.addSeparator()
        
        play_macro_action = QAction('&Play Macro...', self)
        play_macro_action.setShortcut(QKeySequence('Ctrl+Shift+P'))
        play_macro_action.triggered.connect(self.play_macro)
        macro_menu.addAction(play_macro_action)
        
        manage_macros_action = QAction('&Manage Macros...', self)
        manage_macros_action.triggered.connect(self.manage_macros)
        macro_menu.addAction(manage_macros_action)
        
        # Language Menu
        language_menu = menubar.addMenu('&Language')
        self.setup_language_menu(language_menu)
        
    def setup_language_menu(self, menu):
        """Setup the language menu"""
        languages = [
            'Plain Text', 'Python', 'JavaScript', 'TypeScript', 'HTML', 'CSS',
            'JSON', 'XML', 'C', 'C++', 'C#', 'Java', 'PHP', 'Ruby', 'Go',
            'Rust', 'Swift', 'Kotlin', 'SQL', 'Shell', 'PowerShell', 'Batch',
            'Dockerfile', 'YAML', 'TOML', 'Markdown', 'LaTeX', 'R', 'MATLAB',
            'Perl', 'Lua', 'Scala', 'Haskell'
        ]
        
        for language in languages:
            action = QAction(language, self)
            action.triggered.connect(lambda checked, lang=language: self.set_language(lang))
            menu.addAction(action)
    
    def setup_toolbar(self):
        """Setup the toolbar"""
        toolbar = self.addToolBar('Main')
        
        # File operations
        toolbar.addAction('New', self.new_document)
        toolbar.addAction('Open', self.open_file)
        toolbar.addAction('Save', self.save_file)
        toolbar.addSeparator()
        
        # Edit operations
        toolbar.addAction('Undo', self.undo)
        toolbar.addAction('Redo', self.redo)
        toolbar.addSeparator()
        
        # Search operations
        toolbar.addAction('Find', self.show_find_dialog)
        toolbar.addAction('Replace', self.show_replace_dialog)
        toolbar.addSeparator()
        
        # Language selector
        self.language_combo = QComboBox()
        languages = [
            'Plain Text', 'Python', 'JavaScript', 'TypeScript', 'HTML', 'CSS',
            'JSON', 'XML', 'C', 'C++', 'C#', 'Java', 'PHP', 'Ruby', 'Go'
        ]
        self.language_combo.addItems(languages)
        self.language_combo.currentTextChanged.connect(self.set_language)
        toolbar.addWidget(self.language_combo)
        
    def setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = self.statusBar()
        
        # Line/Column info
        self.line_col_label = QLabel("Ln 1, Col 1")
        self.status_bar.addWidget(self.line_col_label)
        
        # Language
        self.language_label = QLabel("Plain Text")
        self.status_bar.addWidget(self.language_label)
        
        # Encoding
        self.encoding_label = QLabel("UTF-8")
        self.status_bar.addWidget(self.encoding_label)
        
        # Modified indicator
        self.modified_label = QLabel("")
        self.status_bar.addWidget(self.modified_label)
        
        # Macro recording indicator
        self.macro_label = QLabel("")
        self.status_bar.addPermanentWidget(self.macro_label)
        
        # File size indicator
        self.file_size_label = QLabel("")
        self.status_bar.addWidget(self.file_size_label)
        
        # Line endings indicator
        self.line_endings_label = QLabel("LF")
        self.status_bar.addWidget(self.line_endings_label)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d30;
                color: #d4d4d4;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                border-bottom: 2px solid #007acc;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
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
        """)
    
    # Document Management
    def new_document(self):
        """Create a new document"""
        self.doc_counter += 1
        doc_id = f"doc_{self.doc_counter}"
        
        # Create document tab
        doc_tab = DocumentTab(self)
        
        # Add to tab widget
        tab_index = self.tab_widget.addTab(doc_tab.editor, f"Untitled {self.doc_counter}")
        self.tab_widget.setCurrentIndex(tab_index)
        
        # Store document
        self.documents[doc_id] = doc_tab
        self.current_doc_id = doc_id
        
        return doc_id
    
    def open_file(self):
        """Open a file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*.*);;Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;"
            "HTML Files (*.html);;CSS Files (*.css);;JSON Files (*.json);;XML Files (*.xml)"
        )
        
        if filepath:
            self.load_file(filepath)
    
    def load_file(self, filepath):
        """Load a file into a new document"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as file:
                        content = file.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                QMessageBox.critical(self, "Error", "Could not decode file with any supported encoding")
                return
            
            # Create new document
            doc_id = self.new_document()
            doc_tab = self.documents[doc_id]
            
            # Set content
            doc_tab.editor.set_content(content)
            doc_tab.filepath = filepath
            doc_tab.encoding = used_encoding
            doc_tab.modified = False
            
            # Detect language
            language = self.detect_language(filepath)
            doc_tab.language = language
            doc_tab.editor.set_language(language)
            
            # Update tab title
            filename = Path(filepath).name
            tab_index = self.tab_widget.currentIndex()
            self.tab_widget.setTabText(tab_index, filename)
            
            # Add to recent files
            self.add_to_recent_files(filepath)
            
            # Watch file for changes
            self.file_watcher.addPath(filepath)
            
            self.update_status_bar(1, 1)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {str(e)}")
    
    def save_file(self):
        """Save current file"""
        if not self.current_doc_id:
            return
            
        doc_tab = self.documents[self.current_doc_id]
        
        if doc_tab.filepath:
            self._save_to_file(doc_tab.filepath)
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """Save current file with new name"""
        if not self.current_doc_id:
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            "",
            "All Files (*.*);;Text Files (*.txt);;Python Files (*.py);;JavaScript Files (*.js);;"
            "HTML Files (*.html);;CSS Files (*.css);;JSON Files (*.json);;XML Files (*.xml)"
        )
        
        if filepath:
            doc_tab = self.documents[self.current_doc_id]
            doc_tab.filepath = filepath
            self._save_to_file(filepath)
            
            # Update tab title
            filename = Path(filepath).name
            tab_index = self.tab_widget.currentIndex()
            self.tab_widget.setTabText(tab_index, filename)
            
            # Detect language
            language = self.detect_language(filepath)
            doc_tab.language = language
            doc_tab.editor.set_language(language)
    
    def _save_to_file(self, filepath):
        """Internal method to save to file"""
        try:
            doc_tab = self.documents[self.current_doc_id]
            
            # Get content from Monaco Editor
            content = doc_tab.editor.get_content()
            
            with open(filepath, 'w', encoding=doc_tab.encoding) as file:
                file.write(content)
            
            doc_tab.modified = False
            self.update_tab_title(doc_tab)
            
            self.statusBar().showMessage(f"Saved: {Path(filepath).name}", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")
    
    def save_all_files(self):
        """Save all modified files"""
        for doc_tab in self.documents.values():
            if doc_tab.modified and doc_tab.filepath:
                # Save logic here
                pass
    
    def close_document(self, index):
        """Close a document tab"""
        # Find document ID for this tab
        doc_id = None
        for did, doc_tab in self.documents.items():
            if self.tab_widget.indexOf(doc_tab.editor) == index:
                doc_id = did
                break
        
        if doc_id:
            doc_tab = self.documents[doc_id]
            
            # Check if modified
            if doc_tab.modified:
                reply = QMessageBox.question(
                    self, "Save Changes",
                    "Do you want to save changes before closing?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Save:
                    self.save_file()
                    if doc_tab.modified:  # Save was cancelled
                        return
            
            # Remove tab
            self.tab_widget.removeTab(index)
            
            # Remove from documents
            del self.documents[doc_id]
            
            # Update current document
            if self.current_doc_id == doc_id:
                if self.documents:
                    self.current_doc_id = list(self.documents.keys())[0]
                else:
                    self.current_doc_id = None
                    self.new_document()  # Create new document if all closed
    
    def close_current_document(self):
        """Close current document"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_document(current_index)
    
    # Event Handlers
    def on_tab_changed(self, index):
        """Handle tab change"""
        if index >= 0:
            # Find document ID for this tab
            for doc_id, doc_tab in self.documents.items():
                if self.tab_widget.indexOf(doc_tab.editor) == index:
                    self.current_doc_id = doc_id
                    self.language_combo.setCurrentText(doc_tab.language)
                    break
    
    def on_file_changed(self, filepath):
        """Handle external file changes"""
        # Find document with this filepath
        for doc_tab in self.documents.values():
            if doc_tab.filepath == filepath:
                reply = QMessageBox.question(
                    self, "File Changed",
                    f"The file {filepath} has been modified externally. Do you want to reload it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.load_file(filepath)
                break
    
    # Editor Operations
    def undo(self):
        """Undo last action"""
        if self.current_doc_id:
            self.documents[self.current_doc_id].editor.undo()
    
    def redo(self):
        """Redo last action"""
        if self.current_doc_id:
            self.documents[self.current_doc_id].editor.redo()
    
    def show_find_dialog(self):
        """Show find dialog"""
        if self.current_doc_id:
            self.documents[self.current_doc_id].editor.find()
    
    def show_replace_dialog(self):
        """Show replace dialog"""
        if self.current_doc_id:
            self.documents[self.current_doc_id].editor.replace()
    
    def show_find_in_files(self):
        """Show find in files dialog"""
        if not self.find_in_files_dialog:
            self.find_in_files_dialog = FindInFilesDialog(self)
        self.find_in_files_dialog.show()
    
    def goto_line(self):
        """Show goto line dialog"""
        if self.current_doc_id:
            self.documents[self.current_doc_id].editor.goto_line()
    
    def toggle_bookmark(self):
        """Toggle bookmark at current line"""
        if self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            if doc_tab.filepath:
                current_line = doc_tab.current_line
                
                result = self.bookmark_manager.toggle_bookmark(
                    doc_tab.filepath, current_line, "User bookmark"
                )
                
                if result:
                    # Add visual bookmark in Monaco
                    doc_tab.editor.page().runJavaScript(
                        f"window.monacoEditor.addBookmark({current_line});"
                    )
                    self.status_bar.showMessage(f"Bookmark added at line {current_line}", 2000)
                else:
                    # Remove visual bookmark in Monaco (would need bookmark ID tracking)
                    self.status_bar.showMessage(f"Bookmark removed from line {current_line}", 2000)
    
    def next_bookmark(self):
        """Go to next bookmark"""
        if self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            if doc_tab.filepath:
                current_line = doc_tab.current_line
                next_bm = self.bookmark_manager.get_next_bookmark(doc_tab.filepath, current_line)
                
                if next_bm:
                    # Jump to bookmark line in Monaco
                    doc_tab.editor.page().runJavaScript(
                        f"window.monacoEditor.setCursorPosition({next_bm.line_number}, 1);"
                    )
                    self.status_bar.showMessage(f"Jumped to bookmark at line {next_bm.line_number}", 2000)
                else:
                    self.status_bar.showMessage("No more bookmarks found", 2000)
    
    def previous_bookmark(self):
        """Go to previous bookmark"""
        if self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            if doc_tab.filepath:
                current_line = doc_tab.current_line
                prev_bm = self.bookmark_manager.get_previous_bookmark(doc_tab.filepath, current_line)
                
                if prev_bm:
                    # Jump to bookmark line in Monaco
                    doc_tab.editor.page().runJavaScript(
                        f"window.monacoEditor.setCursorPosition({prev_bm.line_number}, 1);"
                    )
                    self.status_bar.showMessage(f"Jumped to bookmark at line {prev_bm.line_number}", 2000)
                else:
                    self.status_bar.showMessage("No previous bookmarks found", 2000)
    
    def toggle_word_wrap(self):
        """Toggle word wrap"""
        if self.current_doc_id:
            self.documents[self.current_doc_id].editor.toggle_word_wrap()
    
    def zoom_in(self):
        """Zoom in"""
        if self.current_doc_id:
            self.current_font_size = min(self.current_font_size + 2, 48)
            self._apply_font_size()
    
    def zoom_out(self):
        """Zoom out"""
        if self.current_doc_id:
            self.current_font_size = max(self.current_font_size - 2, 8)
            self._apply_font_size()
    
    def reset_zoom(self):
        """Reset zoom"""
        if self.current_doc_id:
            self.current_font_size = 14
            self._apply_font_size()
            
    def _apply_font_size(self):
        """Apply current font size to active editor"""
        if self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            doc_tab.editor.set_font_size(self.current_font_size)
    
    def set_language(self, language):
        """Set syntax highlighting language"""
        if self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            doc_tab.language = language
            doc_tab.editor.set_language(language)
            self.language_label.setText(language)
    
    # Macro Methods
    def start_macro_recording(self):
        """Start recording a macro"""
        if self.macro_recorder.recording:
            QMessageBox.warning(self, "Warning", "Already recording a macro. Stop current recording first.")
            return
            
        name, ok = QInputDialog.getText(self, "Start Macro Recording", "Macro name:")
        if ok and name:
            self.macro_recorder.start_recording(name)
            self.status_bar.showMessage(f"Started recording macro: {name}", 3000)
            self.update_status_bar(1, 1)  # Refresh status bar
    
    def stop_macro_recording(self):
        """Stop recording current macro"""
        if not self.macro_recorder.recording:
            QMessageBox.information(self, "Information", "No macro is currently being recorded.")
            return
            
        commands = self.macro_recorder.stop_recording()
        self.status_bar.showMessage(f"Stopped recording. Captured {len(commands)} commands.", 3000)
        self.update_status_bar(1, 1)  # Refresh status bar
    
    def play_macro(self):
        """Play a recorded macro"""
        if not self.macro_recorder.macros:
            QMessageBox.information(self, "Information", "No macros available. Record a macro first.")
            return
            
        macro_names = list(self.macro_recorder.macros.keys())
        name, ok = QInputDialog.getItem(self, "Play Macro", "Select macro:", macro_names, 0, False)
        
        if ok and name and self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            self.macro_recorder.play_macro(name, doc_tab.editor)
            self.status_bar.showMessage(f"Played macro: {name}", 3000)
    
    def manage_macros(self):
        """Show macro management dialog"""
        dialog = MacroManagerDialog(self, self.macro_recorder)
        dialog.exec()
    
    # Utility Methods
    def detect_language(self, filepath):
        """Detect programming language from file extension"""
        ext = Path(filepath).suffix.lower()
        
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.xml': 'XML',
            '.c': 'C',
            '.cpp': 'C++',
            '.cxx': 'C++',
            '.cc': 'C++',
            '.cs': 'C#',
            '.java': 'Java',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bash': 'Shell',
            '.ps1': 'PowerShell',
            '.bat': 'Batch',
            '.cmd': 'Batch',
            '.dockerfile': 'Dockerfile',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.toml': 'TOML',
            '.md': 'Markdown',
            '.tex': 'LaTeX',
            '.r': 'R',
            '.m': 'MATLAB',
            '.pl': 'Perl',
            '.lua': 'Lua',
            '.scala': 'Scala',
            '.hs': 'Haskell'
        }
        
        return language_map.get(ext, 'Plain Text')
    
    def add_to_recent_files(self, filepath):
        """Add file to recent files list"""
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        
        self.recent_files.insert(0, filepath)
        
        # Keep only last 10 files
        if len(self.recent_files) > 10:
            self.recent_files = self.recent_files[:10]
    
    def update_recent_files_menu(self, menu):
        """Update recent files menu"""
        menu.clear()
        
        for filepath in self.recent_files:
            action = QAction(filepath, self)
            action.triggered.connect(lambda checked, path=filepath: self.load_file(path))
            menu.addAction(action)
    
    def update_tab_title(self, doc_tab):
        """Update tab title with modification indicator"""
        tab_index = self.tab_widget.indexOf(doc_tab.editor)
        if tab_index >= 0:
            title = self.tab_widget.tabText(tab_index)
            
            # Remove existing modification indicator
            if title.endswith(' *'):
                title = title[:-2]
            
            # Add modification indicator if needed
            if doc_tab.modified:
                title += ' *'
            
            self.tab_widget.setTabText(tab_index, title)
    
    def update_status_bar(self, line, column):
        """Update status bar information"""
        self.line_col_label.setText(f"Ln {line}, Col {column}")
        
        if self.current_doc_id:
            doc_tab = self.documents[self.current_doc_id]
            self.language_label.setText(doc_tab.language)
            self.encoding_label.setText(doc_tab.encoding)
            self.modified_label.setText("Modified" if doc_tab.modified else "")
            
            # Update file size
            if doc_tab.filepath and Path(doc_tab.filepath).exists():
                file_size = Path(doc_tab.filepath).stat().st_size
                self.file_size_label.setText(format_file_size(file_size))
            else:
                self.file_size_label.setText("")
            
            # Update macro recording status
            if self.macro_recorder.recording:
                self.macro_label.setText(f"Recording: {self.macro_recorder.macro_name}")
                self.macro_label.setStyleSheet("color: red; font-weight: bold;")
            else:
                self.macro_label.setText("")
                self.macro_label.setStyleSheet("")
            
            # Update line endings (would need content from Monaco)
            # self.line_endings_label.setText(detect_line_endings(content))


class MacroManagerDialog(QDialog):
    """Dialog for managing saved macros"""
    
    def __init__(self, parent, macro_recorder):
        super().__init__(parent)
        self.macro_recorder = macro_recorder
        self.setup_ui()
        self.load_macros()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Macro Manager")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Macro list
        self.macro_list = QListWidget()
        layout.addWidget(QLabel("Saved Macros:"))
        layout.addWidget(self.macro_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.export_btn = QPushButton("Export")
        self.import_btn = QPushButton("Import")
        self.close_btn = QPushButton("Close")
        
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.rename_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Connect signals
        self.play_btn.clicked.connect(self.play_selected)
        self.rename_btn.clicked.connect(self.rename_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.export_btn.clicked.connect(self.export_macros)
        self.import_btn.clicked.connect(self.import_macros)
        self.close_btn.clicked.connect(self.close)
        
    def load_macros(self):
        """Load macros into the list"""
        self.macro_list.clear()
        for name, commands in self.macro_recorder.macros.items():
            item = QListWidgetItem(f"{name} ({len(commands)} commands)")
            item.setData(Qt.UserRole, name)
            self.macro_list.addItem(item)
            
    def play_selected(self):
        """Play selected macro"""
        current_item = self.macro_list.currentItem()
        if current_item:
            macro_name = current_item.data(Qt.UserRole)
            # Would need reference to current editor
            QMessageBox.information(self, "Info", f"Would play macro: {macro_name}")
            
    def rename_selected(self):
        """Rename selected macro"""
        current_item = self.macro_list.currentItem()
        if current_item:
            old_name = current_item.data(Qt.UserRole)
            new_name, ok = QInputDialog.getText(self, "Rename Macro", "New name:", text=old_name)
            
            if ok and new_name and new_name != old_name:
                if new_name in self.macro_recorder.macros:
                    QMessageBox.warning(self, "Warning", "A macro with this name already exists.")
                    return
                    
                # Rename the macro
                self.macro_recorder.macros[new_name] = self.macro_recorder.macros.pop(old_name)
                self.load_macros()
                
    def delete_selected(self):
        """Delete selected macro"""
        current_item = self.macro_list.currentItem()
        if current_item:
            macro_name = current_item.data(Qt.UserRole)
            reply = QMessageBox.question(
                self, "Confirm Delete", 
                f"Are you sure you want to delete the macro '{macro_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self.macro_recorder.macros[macro_name]
                self.load_macros()
                
    def export_macros(self):
        """Export macros to file"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Macros", "macros.json", "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.macro_recorder.macros, f, indent=2)
                QMessageBox.information(self, "Success", "Macros exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export macros: {e}")
                
    def import_macros(self):
        """Import macros from file"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Macros", "", "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    imported_macros = json.load(f)
                    
                # Merge with existing macros
                for name, commands in imported_macros.items():
                    if name in self.macro_recorder.macros:
                        reply = QMessageBox.question(
                            self, "Macro Exists",
                            f"Macro '{name}' already exists. Overwrite?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            continue
                    
                    self.macro_recorder.macros[name] = commands
                    
                self.load_macros()
                QMessageBox.information(self, "Success", "Macros imported successfully.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import macros: {e}")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MediaHub Ultimate Text Editor")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MediaHub")
    
    # Create and show the editor
    editor = AdvancedTextEditor()
    editor.show()
    
    # Start the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
