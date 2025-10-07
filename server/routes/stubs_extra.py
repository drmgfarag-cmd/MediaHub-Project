from flask import Blueprint, jsonify, request
stubs_bp = Blueprint('stubs_extra', __name__)

@stubs_bp.route('/api/backup/restore')
def backup_restore():
    name = request.args.get('name','')
    return jsonify({'ok': True, 'restored': False, 'name': name})

@stubs_bp.route('/api/collections/')
def collections_root():
    return jsonify({'ok': True, 'collections': []})

@stubs_bp.route('/api/collections/rest')
def collections_rest():
    cat = request.args.get('category','')
    return jsonify({'ok': True, 'category': cat, 'items': []})

@stubs_bp.route('/api/library/item/')
def lib_item():
    return jsonify({'ok': True, 'item': {}})

@stubs_bp.route('/api/library/search')
def lib_search():
    q = request.args.get('q','')
    return jsonify({'ok': True, 'query': q, 'items': []})

@stubs_bp.route('/api/library/title/')
def lib_title():
    t = request.args.get('t','')
    return jsonify({'ok': True, 'title': t, 'items': []})

@stubs_bp.route('/api/reader/cbz_pages')
def cbz_pages():
    path = request.args.get('path','')
    return jsonify({'ok': True, 'path': path, 'pages': []})

@stubs_bp.route('/api/trailer/hero')
def trailer_hero():
    cat = request.args.get('category','')
    return jsonify({'ok': True, 'category': cat, 'trailers': []})
