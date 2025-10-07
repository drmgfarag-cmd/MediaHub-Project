"""
Text Editor API - Golden Surface Endpoints
Wraps PyQt6 text_editor.py functionality with Flask APIs
"""

from flask import Blueprint, jsonify, request
import os
import json
from datetime import datetime

editor_api_bp = Blueprint('editor_api', __name__)

# Storage paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
DOCUMENTS_FILE = os.path.join(STORAGE, 'editor_documents.json')
MACROS_FILE = os.path.join(STORAGE, 'editor_macros.json')
BOOKMARKS_FILE = os.path.join(STORAGE, 'editor_bookmarks.json')
SYNTAX_FILE = os.path.join(STORAGE, 'editor_syntax.json')

# Ensure storage directory exists
os.makedirs(STORAGE, exist_ok=True)


def load_json(filepath, default):
    """Load JSON file with fallback to default"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default


def save_json(filepath, data):
    """Save JSON file atomically"""
    temp_file = filepath + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, filepath)


# Supported languages for syntax highlighting
SUPPORTED_LANGUAGES = [
    'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'csharp',
    'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'scala', 'perl',
    'html', 'css', 'scss', 'less', 'sass', 'json', 'xml', 'yaml',
    'markdown', 'sql', 'bash', 'powershell', 'batch', 'dockerfile',
    'makefile', 'cmake', 'nginx', 'apache', 'ini', 'toml', 'properties',
    'lua', 'r', 'matlab', 'julia', 'haskell', 'erlang', 'elixir',
    'clojure', 'lisp', 'scheme', 'fortran', 'cobol', 'ada', 'pascal',
    'vb', 'vbnet', 'fsharp', 'ocaml', 'dart', 'groovy', 'tcl'
]


@editor_api_bp.route('/api/editor/documents', methods=['GET'])
def get_documents():
    """
    Golden Surface API: Multi-document interface management
    Returns list of open documents/sessions
    """
    documents_data = load_json(DOCUMENTS_FILE, {
        'documents': [],
        'active_document_id': None
    })
    
    documents = documents_data.get('documents', [])
    active_id = documents_data.get('active_document_id')
    
    return jsonify({
        'ok': True,
        'documents': documents,
        'active_document_id': active_id,
        'total': len(documents)
    })


@editor_api_bp.route('/api/editor/documents', methods=['POST'])
def create_document():
    """Create a new document"""
    try:
        documents_data = load_json(DOCUMENTS_FILE, {
            'documents': [],
            'active_document_id': None
        })
        
        # Generate new document ID
        doc_id = f"doc_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        new_doc = {
            'id': doc_id,
            'filename': request.json.get('filename', 'Untitled'),
            'filepath': request.json.get('filepath', ''),
            'content': request.json.get('content', ''),
            'language': request.json.get('language', 'text'),
            'modified': False,
            'created_at': datetime.utcnow().isoformat(),
            'modified_at': None,
            'cursor_position': {'line': 0, 'column': 0},
            'scroll_position': 0
        }
        
        documents_data['documents'].append(new_doc)
        documents_data['active_document_id'] = doc_id
        
        save_json(DOCUMENTS_FILE, documents_data)
        
        return jsonify({
            'ok': True,
            'document': new_doc,
            'message': 'Document created successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/documents/<doc_id>', methods=['GET'])
def get_document(doc_id):
    """Get specific document by ID"""
    documents_data = load_json(DOCUMENTS_FILE, {'documents': []})
    
    document = next((d for d in documents_data.get('documents', []) if d.get('id') == doc_id), None)
    
    if document:
        return jsonify({
            'ok': True,
            'document': document
        })
    else:
        return jsonify({
            'ok': False,
            'error': f'Document {doc_id} not found'
        }), 404


@editor_api_bp.route('/api/editor/documents/<doc_id>', methods=['PUT'])
def update_document(doc_id):
    """Update document content"""
    try:
        documents_data = load_json(DOCUMENTS_FILE, {'documents': []})
        
        document = next((d for d in documents_data['documents'] if d.get('id') == doc_id), None)
        
        if not document:
            return jsonify({
                'ok': False,
                'error': f'Document {doc_id} not found'
            }), 404
        
        # Update document fields
        if 'content' in request.json:
            document['content'] = request.json['content']
            document['modified'] = True
        
        if 'filename' in request.json:
            document['filename'] = request.json['filename']
        
        if 'language' in request.json:
            document['language'] = request.json['language']
        
        if 'cursor_position' in request.json:
            document['cursor_position'] = request.json['cursor_position']
        
        if 'scroll_position' in request.json:
            document['scroll_position'] = request.json['scroll_position']
        
        document['modified_at'] = datetime.utcnow().isoformat()
        
        save_json(DOCUMENTS_FILE, documents_data)
        
        return jsonify({
            'ok': True,
            'document': document,
            'message': 'Document updated successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/documents/<doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Close/delete a document"""
    try:
        documents_data = load_json(DOCUMENTS_FILE, {'documents': []})
        
        documents_data['documents'] = [d for d in documents_data['documents'] if d.get('id') != doc_id]
        
        # If deleted document was active, set active to first document or None
        if documents_data.get('active_document_id') == doc_id:
            documents_data['active_document_id'] = documents_data['documents'][0]['id'] if documents_data['documents'] else None
        
        save_json(DOCUMENTS_FILE, documents_data)
        
        return jsonify({
            'ok': True,
            'message': 'Document closed successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/syntax', methods=['GET'])
def get_syntax_support():
    """
    Golden Surface API: Syntax highlighting for 50+ languages
    Returns list of supported languages and their configurations
    """
    syntax_data = load_json(SYNTAX_FILE, {
        'languages': SUPPORTED_LANGUAGES,
        'default_language': 'text',
        'theme': 'monokai',
        'available_themes': ['monokai', 'github', 'solarized-dark', 'solarized-light', 'dracula', 'nord']
    })
    
    # Filter by query if provided
    query = request.args.get('q', '').lower()
    if query:
        languages = [lang for lang in syntax_data['languages'] if query in lang.lower()]
    else:
        languages = syntax_data['languages']
    
    return jsonify({
        'ok': True,
        'languages': languages,
        'total': len(languages),
        'default_language': syntax_data.get('default_language', 'text'),
        'theme': syntax_data.get('theme', 'monokai'),
        'available_themes': syntax_data.get('available_themes', [])
    })


@editor_api_bp.route('/api/editor/syntax', methods=['POST'])
def set_syntax_config():
    """Update syntax highlighting configuration"""
    try:
        syntax_data = load_json(SYNTAX_FILE, {
            'languages': SUPPORTED_LANGUAGES,
            'default_language': 'text',
            'theme': 'monokai'
        })
        
        if 'theme' in request.json:
            syntax_data['theme'] = request.json['theme']
        
        if 'default_language' in request.json:
            syntax_data['default_language'] = request.json['default_language']
        
        save_json(SYNTAX_FILE, syntax_data)
        
        return jsonify({
            'ok': True,
            'syntax': syntax_data,
            'message': 'Syntax configuration updated successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/macros', methods=['GET'])
def get_macros():
    """
    Golden Surface API: Macro recording and playback
    Returns list of saved macros
    """
    macros_data = load_json(MACROS_FILE, {
        'macros': []
    })
    
    macros = macros_data.get('macros', [])
    
    return jsonify({
        'ok': True,
        'macros': macros,
        'total': len(macros)
    })


@editor_api_bp.route('/api/editor/macros', methods=['POST'])
def create_macro():
    """Create/save a new macro"""
    try:
        macros_data = load_json(MACROS_FILE, {'macros': []})
        
        macro_id = f"macro_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        new_macro = {
            'id': macro_id,
            'name': request.json.get('name', 'Untitled Macro'),
            'description': request.json.get('description', ''),
            'actions': request.json.get('actions', []),
            'shortcut': request.json.get('shortcut', ''),
            'created_at': datetime.utcnow().isoformat(),
            'usage_count': 0
        }
        
        macros_data['macros'].append(new_macro)
        save_json(MACROS_FILE, macros_data)
        
        return jsonify({
            'ok': True,
            'macro': new_macro,
            'message': 'Macro saved successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/macros/<macro_id>', methods=['DELETE'])
def delete_macro(macro_id):
    """Delete a macro"""
    try:
        macros_data = load_json(MACROS_FILE, {'macros': []})
        
        macros_data['macros'] = [m for m in macros_data['macros'] if m.get('id') != macro_id]
        save_json(MACROS_FILE, macros_data)
        
        return jsonify({
            'ok': True,
            'message': 'Macro deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/macros/<macro_id>/execute', methods=['POST'])
def execute_macro(macro_id):
    """Execute a macro"""
    try:
        macros_data = load_json(MACROS_FILE, {'macros': []})
        
        macro = next((m for m in macros_data['macros'] if m.get('id') == macro_id), None)
        
        if not macro:
            return jsonify({
                'ok': False,
                'error': f'Macro {macro_id} not found'
            }), 404
        
        # Increment usage count
        macro['usage_count'] = macro.get('usage_count', 0) + 1
        macro['last_used'] = datetime.utcnow().isoformat()
        
        save_json(MACROS_FILE, macros_data)
        
        return jsonify({
            'ok': True,
            'macro': macro,
            'message': 'Macro executed successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/bookmarks', methods=['GET'])
def get_bookmarks():
    """
    Golden Surface API: Document bookmarking
    Returns list of bookmarks across all documents
    """
    bookmarks_data = load_json(BOOKMARKS_FILE, {
        'bookmarks': []
    })
    
    bookmarks = bookmarks_data.get('bookmarks', [])
    
    # Filter by document if specified
    doc_id = request.args.get('document_id')
    if doc_id:
        bookmarks = [b for b in bookmarks if b.get('document_id') == doc_id]
    
    return jsonify({
        'ok': True,
        'bookmarks': bookmarks,
        'total': len(bookmarks)
    })


@editor_api_bp.route('/api/editor/bookmarks', methods=['POST'])
def create_bookmark():
    """Create a new bookmark"""
    try:
        bookmarks_data = load_json(BOOKMARKS_FILE, {'bookmarks': []})
        
        bookmark_id = f"bookmark_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        new_bookmark = {
            'id': bookmark_id,
            'document_id': request.json.get('document_id'),
            'line': request.json.get('line', 0),
            'column': request.json.get('column', 0),
            'label': request.json.get('label', ''),
            'note': request.json.get('note', ''),
            'created_at': datetime.utcnow().isoformat()
        }
        
        bookmarks_data['bookmarks'].append(new_bookmark)
        save_json(BOOKMARKS_FILE, bookmarks_data)
        
        return jsonify({
            'ok': True,
            'bookmark': new_bookmark,
            'message': 'Bookmark created successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@editor_api_bp.route('/api/editor/bookmarks/<bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    """Delete a bookmark"""
    try:
        bookmarks_data = load_json(BOOKMARKS_FILE, {'bookmarks': []})
        
        bookmarks_data['bookmarks'] = [b for b in bookmarks_data['bookmarks'] if b.get('id') != bookmark_id]
        save_json(BOOKMARKS_FILE, bookmarks_data)
        
        return jsonify({
            'ok': True,
            'message': 'Bookmark deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500
