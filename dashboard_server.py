#!/usr/bin/env python3.11
"""
Standalone Flask server for MediaHub Dashboard Customization Features
This server provides the backend APIs for tree hierarchy and pinned cards
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration paths
ROOT = os.path.abspath(os.path.dirname(__file__))
STO = os.path.join(ROOT, 'storage')
DASHBOARD_CONFIG = os.path.join(STO, 'config', 'dashboard_config.json')

def _load_dashboard_config():
    """Load dashboard configuration"""
    try:
        with open(DASHBOARD_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'tree_hierarchy': {
                'movies': {
                    'enabled': True,
                    'nodes': [
                        {'id': 'movies_all', 'label': 'All Movies', 'parent': None, 'type': 'root'},
                        {'id': 'movies_genres', 'label': 'Genres', 'parent': 'movies_all', 'type': 'folder'},
                        {'id': 'movies_years', 'label': 'Years', 'parent': 'movies_all', 'type': 'folder'},
                        {'id': 'movies_collections', 'label': 'Collections', 'parent': 'movies_all', 'type': 'folder'},
                        {'id': 'movies_quality', 'label': 'Quality', 'parent': 'movies_all', 'type': 'folder'}
                    ]
                },
                'tv_shows': {
                    'enabled': True,
                    'nodes': [
                        {'id': 'tv_all', 'label': 'All TV Shows', 'parent': None, 'type': 'root'},
                        {'id': 'tv_genres', 'label': 'Genres', 'parent': 'tv_all', 'type': 'folder'},
                        {'id': 'tv_networks', 'label': 'Networks', 'parent': 'tv_all', 'type': 'folder'},
                        {'id': 'tv_status', 'label': 'Status', 'parent': 'tv_all', 'type': 'folder'}
                    ]
                },
                'books': {
                    'enabled': True,
                    'nodes': [
                        {'id': 'books_all', 'label': 'All Books', 'parent': None, 'type': 'root'},
                        {'id': 'books_authors', 'label': 'Authors', 'parent': 'books_all', 'type': 'folder'},
                        {'id': 'books_genres', 'label': 'Genres', 'parent': 'books_all', 'type': 'folder'},
                        {'id': 'books_series', 'label': 'Series', 'parent': 'books_all', 'type': 'folder'},
                        {'id': 'books_collections', 'label': 'Collections', 'parent': 'books_all', 'type': 'folder'}
                    ]
                },
                'audio': {
                    'enabled': True,
                    'nodes': [
                        {'id': 'audio_all', 'label': 'All Audio', 'parent': None, 'type': 'root'},
                        {'id': 'audio_artists', 'label': 'Artists', 'parent': 'audio_all', 'type': 'folder'},
                        {'id': 'audio_albums', 'label': 'Albums', 'parent': 'audio_all', 'type': 'folder'},
                        {'id': 'audio_genres', 'label': 'Genres', 'parent': 'audio_all', 'type': 'folder'},
                        {'id': 'audio_playlists', 'label': 'Playlists', 'parent': 'audio_all', 'type': 'folder'}
                    ]
                }
            },
            'pinned_cards': [
                {
                    'id': 'movies_card',
                    'category': 'movies',
                    'title': 'Movies',
                    'icon': 'film',
                    'color': '#e50914',
                    'position': 0,
                    'enabled': True,
                    'quick_links': [
                        {'label': 'Recently Added', 'path': '/movies?sort=added'},
                        {'label': 'Top Rated', 'path': '/movies?sort=rating'},
                        {'label': '4K Collection', 'path': '/movies?quality=4k'}
                    ]
                },
                {
                    'id': 'tv_shows_card',
                    'category': 'tv_shows',
                    'title': 'TV Shows',
                    'icon': 'tv',
                    'color': '#0080ff',
                    'position': 1,
                    'enabled': True,
                    'quick_links': [
                        {'label': 'Continue Watching', 'path': '/tv?filter=watching'},
                        {'label': 'New Episodes', 'path': '/tv?filter=new_episodes'},
                        {'label': 'Airing Today', 'path': '/tv?filter=airing_today'}
                    ]
                },
                {
                    'id': 'books_card',
                    'category': 'books',
                    'title': 'Books',
                    'icon': 'book',
                    'color': '#ff9500',
                    'position': 2,
                    'enabled': True,
                    'quick_links': [
                        {'label': 'Currently Reading', 'path': '/books?filter=reading'},
                        {'label': 'To Read', 'path': '/books?filter=to_read'},
                        {'label': 'Finished', 'path': '/books?filter=finished'}
                    ]
                },
                {
                    'id': 'audio_card',
                    'category': 'audio',
                    'title': 'Audio',
                    'icon': 'music',
                    'color': '#1db954',
                    'position': 3,
                    'enabled': True,
                    'quick_links': [
                        {'label': 'Recently Played', 'path': '/audio?sort=played'},
                        {'label': 'Top Tracks', 'path': '/audio?sort=rating'},
                        {'label': 'Playlists', 'path': '/audio/playlists'}
                    ]
                }
            ],
            'layout_preferences': {
                'card_size': 'medium',
                'cards_per_row': 4,
                'show_stats': True,
                'show_quick_links': True,
                'theme': 'dark'
            }
        }

def _save_dashboard_config(data):
    """Save dashboard configuration"""
    os.makedirs(os.path.dirname(DASHBOARD_CONFIG), exist_ok=True)
    tmp = DASHBOARD_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, DASHBOARD_CONFIG)

@app.route('/api/dashboard/config', methods=['GET'])
def get_dashboard_config():
    """Get dashboard configuration"""
    config = _load_dashboard_config()
    return jsonify({
        'ok': True,
        'config': config
    })

@app.route('/api/dashboard/config', methods=['POST'])
def update_dashboard_config():
    """Update dashboard configuration"""
    req_data = request.get_json(silent=True) or {}
    
    config = _load_dashboard_config()
    
    # Update specific sections
    if 'tree_hierarchy' in req_data:
        config['tree_hierarchy'] = req_data['tree_hierarchy']
    if 'pinned_cards' in req_data:
        config['pinned_cards'] = req_data['pinned_cards']
    if 'layout_preferences' in req_data:
        config['layout_preferences'] = req_data['layout_preferences']
    
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Dashboard configuration updated',
        'config': config
    })

@app.route('/api/dashboard/tree/<category>', methods=['GET'])
def get_tree_hierarchy(category):
    """Get tree hierarchy for a specific category"""
    config = _load_dashboard_config()
    tree = config.get('tree_hierarchy', {}).get(category, {})
    
    if not tree:
        return jsonify({'ok': False, 'error': 'Category not found'}), 404
    
    return jsonify({
        'ok': True,
        'category': category,
        'tree': tree
    })

@app.route('/api/dashboard/tree/<category>/nodes', methods=['POST'])
def add_tree_node(category):
    """Add a node to tree hierarchy"""
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('id') or not req_data.get('label'):
        return jsonify({'ok': False, 'error': 'id and label required'}), 400
    
    config = _load_dashboard_config()
    
    if category not in config['tree_hierarchy']:
        return jsonify({'ok': False, 'error': 'Category not found'}), 404
    
    node = {
        'id': req_data.get('id'),
        'label': req_data.get('label'),
        'parent': req_data.get('parent'),
        'type': req_data.get('type', 'folder'),
        'icon': req_data.get('icon', ''),
        'metadata': req_data.get('metadata', {})
    }
    
    config['tree_hierarchy'][category]['nodes'].append(node)
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Node added',
        'node': node
    })

@app.route('/api/dashboard/tree/<category>/nodes/<node_id>', methods=['PUT'])
def update_tree_node(category, node_id):
    """Update a tree node"""
    req_data = request.get_json(silent=True) or {}
    
    config = _load_dashboard_config()
    
    if category not in config['tree_hierarchy']:
        return jsonify({'ok': False, 'error': 'Category not found'}), 404
    
    nodes = config['tree_hierarchy'][category]['nodes']
    node = next((n for n in nodes if n.get('id') == node_id), None)
    
    if not node:
        return jsonify({'ok': False, 'error': 'Node not found'}), 404
    
    # Update node fields
    for key in ['label', 'parent', 'type', 'icon', 'metadata']:
        if key in req_data:
            node[key] = req_data[key]
    
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Node updated',
        'node': node
    })

@app.route('/api/dashboard/tree/<category>/nodes/<node_id>', methods=['DELETE'])
def delete_tree_node(category, node_id):
    """Delete a tree node"""
    config = _load_dashboard_config()
    
    if category not in config['tree_hierarchy']:
        return jsonify({'ok': False, 'error': 'Category not found'}), 404
    
    nodes = config['tree_hierarchy'][category]['nodes']
    original_count = len(nodes)
    
    # Remove node and its children
    nodes_to_remove = [node_id]
    
    # Find all children recursively
    def find_children(parent_id):
        children = [n['id'] for n in nodes if n.get('parent') == parent_id]
        for child_id in children:
            nodes_to_remove.append(child_id)
            find_children(child_id)
    
    find_children(node_id)
    
    # Remove all identified nodes
    config['tree_hierarchy'][category]['nodes'] = [n for n in nodes if n['id'] not in nodes_to_remove]
    
    if len(config['tree_hierarchy'][category]['nodes']) == original_count:
        return jsonify({'ok': False, 'error': 'Node not found'}), 404
    
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': f'Node and {len(nodes_to_remove) - 1} children deleted'
    })

@app.route('/api/dashboard/pinned-cards', methods=['GET'])
def get_pinned_cards():
    """Get all pinned cards"""
    config = _load_dashboard_config()
    cards = config.get('pinned_cards', [])
    
    # Sort by position
    cards.sort(key=lambda x: x.get('position', 0))
    
    return jsonify({
        'ok': True,
        'cards': cards,
        'total': len(cards)
    })

@app.route('/api/dashboard/pinned-cards/<card_id>', methods=['PUT'])
def update_pinned_card(card_id):
    """Update a pinned card"""
    req_data = request.get_json(silent=True) or {}
    
    config = _load_dashboard_config()
    cards = config.get('pinned_cards', [])
    
    card = next((c for c in cards if c.get('id') == card_id), None)
    
    if not card:
        return jsonify({'ok': False, 'error': 'Card not found'}), 404
    
    # Update card fields
    for key in ['title', 'icon', 'color', 'position', 'enabled', 'quick_links']:
        if key in req_data:
            card[key] = req_data[key]
    
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Card updated',
        'card': card
    })

@app.route('/api/dashboard/pinned-cards/<card_id>/toggle', methods=['POST'])
def toggle_pinned_card(card_id):
    """Toggle card enabled/disabled"""
    config = _load_dashboard_config()
    cards = config.get('pinned_cards', [])
    
    card = next((c for c in cards if c.get('id') == card_id), None)
    
    if not card:
        return jsonify({'ok': False, 'error': 'Card not found'}), 404
    
    card['enabled'] = not card.get('enabled', True)
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': f"Card {'enabled' if card['enabled'] else 'disabled'}",
        'card': card
    })

@app.route('/api/dashboard/layout', methods=['GET'])
def get_layout_preferences():
    """Get layout preferences"""
    config = _load_dashboard_config()
    layout = config.get('layout_preferences', {})
    
    return jsonify({
        'ok': True,
        'layout': layout
    })

@app.route('/api/dashboard/layout', methods=['POST'])
def update_layout_preferences():
    """Update layout preferences"""
    req_data = request.get_json(silent=True) or {}
    
    config = _load_dashboard_config()
    layout = config.get('layout_preferences', {})
    
    # Update layout fields
    for key in ['card_size', 'cards_per_row', 'show_stats', 'show_quick_links', 'theme']:
        if key in req_data:
            layout[key] = req_data[key]
    
    config['layout_preferences'] = layout
    _save_dashboard_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Layout preferences updated',
        'layout': layout
    })

if __name__ == '__main__':
    print("Starting MediaHub Dashboard Server on http://localhost:5000")
    print("CORS enabled for frontend communication")
    app.run(host='0.0.0.0', port=5000, debug=True)
