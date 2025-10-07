"""
Phase 5: Advanced UI & User Experience
Implements modern UI components, themes, accessibility, and enhanced user experience features
"""

from flask import Blueprint, request, jsonify, render_template_string
import os
import json
import sqlite3
from datetime import datetime, timedelta
import base64

advanced_ui_bp = Blueprint('advanced_ui', __name__)

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
UI_DB = os.path.join(STORAGE, 'advanced_ui.db')
THEMES_DIR = os.path.join(ROOT, 'web', 'themes')

def init_advanced_ui_db():
    """Initialize advanced UI database"""
    conn = sqlite3.connect(UI_DB)
    cursor = conn.cursor()
    
    # User preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            theme_name TEXT DEFAULT 'dark',
            language TEXT DEFAULT 'en',
            timezone TEXT DEFAULT 'UTC',
            date_format TEXT DEFAULT 'YYYY-MM-DD',
            time_format TEXT DEFAULT '24h',
            grid_view_size TEXT DEFAULT 'medium', -- small, medium, large
            list_view_density TEXT DEFAULT 'comfortable', -- compact, comfortable, spacious
            auto_play_trailers BOOLEAN DEFAULT FALSE,
            show_adult_content BOOLEAN DEFAULT FALSE,
            accessibility_mode BOOLEAN DEFAULT FALSE,
            high_contrast BOOLEAN DEFAULT FALSE,
            reduced_motion BOOLEAN DEFAULT FALSE,
            font_size TEXT DEFAULT 'normal', -- small, normal, large, extra-large
            sidebar_collapsed BOOLEAN DEFAULT FALSE,
            dashboard_layout TEXT DEFAULT 'default', -- JSON layout config
            quick_actions TEXT DEFAULT '[]', -- JSON array of enabled quick actions
            notification_settings TEXT DEFAULT '{}', -- JSON notification preferences
            keyboard_shortcuts TEXT DEFAULT '{}', -- JSON custom shortcuts
            privacy_settings TEXT DEFAULT '{}', -- JSON privacy preferences
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Themes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            author TEXT,
            version TEXT DEFAULT '1.0.0',
            css_content TEXT NOT NULL,
            js_content TEXT,
            config_json TEXT, -- Theme configuration options
            preview_image TEXT, -- Base64 encoded preview
            is_built_in BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT FALSE,
            download_count INTEGER DEFAULT 0,
            rating REAL DEFAULT 0.0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # UI components and layouts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ui_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component_name TEXT UNIQUE NOT NULL,
            component_type TEXT NOT NULL, -- widget, layout, modal, etc.
            html_template TEXT NOT NULL,
            css_styles TEXT,
            js_behavior TEXT,
            config_schema TEXT, -- JSON schema for configuration
            default_config TEXT, -- JSON default configuration
            is_enabled BOOLEAN DEFAULT TRUE,
            sort_order INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Dashboard layouts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dashboard_layouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            layout_name TEXT NOT NULL,
            layout_config TEXT NOT NULL, -- JSON layout configuration
            is_default BOOLEAN DEFAULT FALSE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT DEFAULT 'info', -- info, success, warning, error
            category TEXT, -- download, system, update, etc.
            action_url TEXT,
            action_text TEXT,
            is_read BOOLEAN DEFAULT FALSE,
            is_persistent BOOLEAN DEFAULT FALSE,
            expires_at TIMESTAMP,
            metadata_json TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # User activity and analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            action_type TEXT NOT NULL, -- page_view, search, download, etc.
            action_target TEXT, -- what was acted upon
            action_details TEXT, -- JSON details
            ip_address TEXT,
            user_agent TEXT,
            session_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Keyboard shortcuts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyboard_shortcuts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            action_name TEXT NOT NULL,
            key_combination TEXT NOT NULL,
            description TEXT,
            is_enabled BOOLEAN DEFAULT TRUE,
            is_custom BOOLEAN DEFAULT FALSE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activity_user_time ON user_activity(user_id, timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_shortcuts_user ON keyboard_shortcuts(user_id)')
    
    conn.commit()
    conn.close()

# Initialize database and create default data
init_advanced_ui_db()

@advanced_ui_bp.route('/api/ui/preferences')
def get_user_preferences():
    """Get user preferences"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_preferences WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            columns = [description[0] for description in cursor.description]
            preferences = dict(zip(columns, result))
            
            # Parse JSON fields
            for field in ['dashboard_layout', 'quick_actions', 'notification_settings', 
                         'keyboard_shortcuts', 'privacy_settings']:
                if preferences.get(field):
                    try:
                        preferences[field] = json.loads(preferences[field])
                    except:
                        preferences[field] = {} if field.endswith('_settings') else []
        else:
            # Create default preferences
            preferences = create_default_preferences(cursor, user_id)
        
        conn.commit()
        conn.close()
        
                        return jsonify(preferences)
        
    except Exception as e:
                        return jsonify({'error': str(e)}), 500

# DUPLICATE REMOVED: @advanced_ui_bp.route('/api/ui/preferences', methods=['POST'])
def create_ui_preferences():
    """Create Preferences"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_ui_preferences():
    """Create Preferences"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def update_user_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        # Check if preferences exist
        cursor.execute('SELECT id FROM user_preferences WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing preferences
            update_fields = []
            params = []
            
            for field in ['theme_name', 'language', 'timezone', 'date_format', 'time_format',
                         'grid_view_size', 'list_view_density', 'auto_play_trailers', 
                         'show_adult_content', 'accessibility_mode', 'high_contrast',
                         'reduced_motion', 'font_size', 'sidebar_collapsed']:
                if field in data:
                    update_fields.append(f'{field} = ?')
                    params.append(data[field])
            
            # Handle JSON fields
            for field in ['dashboard_layout', 'quick_actions', 'notification_settings',
                         'keyboard_shortcuts', 'privacy_settings']:
                if field in data:
                    update_fields.append(f'{field} = ?')
                    params.append(json.dumps(data[field]))
            
            if update_fields:
                update_fields.append('updated_date = CURRENT_TIMESTAMP')
                params.append(user_id)
                
                query = f'UPDATE user_preferences SET {", ".join(update_fields)} WHERE user_id = ?'
                cursor.execute(query, params)
        else:
            # Create new preferences
            create_default_preferences(cursor, user_id, data)
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Preferences updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/themes')
def get_themes():
    """Get available themes"""
    try:
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, display_name, description, author, version, 
                   preview_image, is_built_in, is_active, rating
            FROM themes
            ORDER BY is_built_in DESC, rating DESC, name
        ''')
        
        columns = [description[0] for description in cursor.description]
        themes = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(themes)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/themes/<theme_name>')
def get_theme_details(theme_name):
    """Get theme details including CSS content"""
    try:
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM themes WHERE name = ?', (theme_name,))
        result = cursor.fetchone()
        
        if not result:
        return jsonify({'error': 'Theme not found'}), 404
        
        columns = [description[0] for description in cursor.description]
        theme = dict(zip(columns, result))
        
        # Parse config JSON
        if theme.get('config_json'):
            try:
                theme['config'] = json.loads(theme['config_json'])
            except:
                theme['config'] = {}
        
        conn.close()
                return jsonify(theme)
        
    except Exception as e:
                return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/themes/<theme_name>/activate', methods=['POST'])
def activate_theme(theme_name):
    """Activate a theme"""
    try:
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        # Deactivate all themes
        cursor.execute('UPDATE themes SET is_active = FALSE')
        
        # Activate selected theme
        cursor.execute('UPDATE themes SET is_active = TRUE WHERE name = ?', (theme_name,))
        
        if cursor.rowcount == 0:
        return jsonify({'error': 'Theme not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Theme {theme_name} activated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/notifications')
def get_notifications():
    """Get user notifications"""
    try:
        user_id = request.args.get('user_id', 'default')
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM notifications 
            WHERE user_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        '''
        params = [user_id]
        
        if unread_only:
            query += ' AND is_read = FALSE'
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY created_date DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        notifications = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse metadata JSON
        for notification in notifications:
            if notification.get('metadata_json'):
                try:
                    notification['metadata'] = json.loads(notification['metadata_json'])
                except:
                    notification['metadata'] = {}
        
        conn.close()
                    return jsonify(notifications)
        
    except Exception as e:
                    return jsonify({'error': str(e)}), 500

# DUPLICATE REMOVED: @advanced_ui_bp.route('/api/ui/notifications', methods=['POST'])
# DUPLICATE REMOVED: def create_notification():
    """Create a new notification"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'message']
        for field in required_fields:
            if not data.get(field):
        return jsonify({'error': f'{field} is required'}), 400
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (
                user_id, title, message, type, category, action_url, action_text,
                is_persistent, expires_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('user_id', 'default'),
            data['title'],
            data['message'],
            data.get('type', 'info'),
            data.get('category'),
            data.get('action_url'),
            data.get('action_text'),
            data.get('is_persistent', False),
            data.get('expires_at'),
            json.dumps(data.get('metadata', {}))
        ))
        
        notification_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': notification_id, 'message': 'Notification created successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET is_read = TRUE WHERE id = ?', (notification_id,))
        
        if cursor.rowcount == 0:
        return jsonify({'error': 'Notification not found'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Notification marked as read'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/dashboard/layouts')
def get_dashboard_layouts():
    """Get available dashboard layouts"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM dashboard_layouts 
            WHERE user_id = ? OR user_id = 'global'
            ORDER BY is_default DESC, layout_name
        ''', (user_id,))
        
        def create_dashboard_layouts():
            """Create Layouts"""
            try:
                data = request.get_json()
                if not data:
                return jsonify({'error': 'No data provided'}), 400
                return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        columns = [description[0] for description in cursor.description]
        layouts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse layout config JSON
        for layout in layouts:
            if layout.get('layout_config'):
                try:
                    layout['config'] = json.loads(layout['layout_config'])
                except:
                def create_dashboard_layouts():
                    """Create Layouts"""
                    try:
                        data = request.get_json()
                        if not data:
                        return jsonify({'error': 'No data provided'}), 400
                        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500
                    layout['config'] = {}
        
        conn.close()
                        return jsonify(layouts)
        
    except Exception as e:
                        return jsonify({'error': str(e)}), 500

# DUPLICATE REMOVED: @advanced_ui_bp.route('/api/ui/dashboard/layouts', methods=['POST'])
# DUPLICATE REMOVED: def save_dashboard_layout():
    """Save dashboard layout"""
    try:
        data = request.get_json()
        
        required_fields = ['layout_name', 'layout_config']
        for field in required_fields:
            if not data.get(field):
        return jsonify({'error': f'{field} is required'}), 400
        
        user_id = data.get('user_id', 'default')
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        # Check if layout exists
        cursor.execute('''
            SELECT id FROM dashboard_layouts 
            WHERE user_id = ? AND layout_name = ?
        ''', (user_id, data['layout_name']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing layout
            cursor.execute('''
                UPDATE dashboard_layouts 
                SET layout_config = ?, updated_date = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (json.dumps(data['layout_config']), existing[0]))
        else:
            # Create new layout
            cursor.execute('''
                INSERT INTO dashboard_layouts (user_id, layout_name, layout_config, is_default)
                VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                data['layout_name'],
                json.dumps(data['layout_config']),
                data.get('is_default', False)
            ))
        
        # If this is set as default, unset others
        if data.get('is_default'):
            cursor.execute('''
                UPDATE dashboard_layouts 
                SET is_default = FALSE 
                def create_ui_keyboard_shortcuts():
                    """Create Keyboard Shortcuts"""
                    try:
                        data = request.get_json()
                        if not data:
                        return jsonify({'error': 'No data provided'}), 400
                        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
                    except Exception as e:
                        return jsonify({'error': str(e)}), 500
                WHERE user_id = ? AND layout_name != ?
            ''', (user_id, data['layout_name']))
        
        conn.commit()
        conn.close()
        
                        return jsonify({'message': 'Dashboard layout saved successfully'})
        
    except Exception as e:
                        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/keyboard-shortcuts')
def get_keyboard_shortcuts():
    """Get keyboard shortcuts"""
    try:
        user_id = request.args.get('user_id', 'default')
        
        conn = sqlite3.connect(UI_DB)
        def create_ui_keyboard_shortcuts():
            """Create Keyboard Shortcuts"""
            try:
                data = request.get_json()
                if not data:
                return jsonify({'error': 'No data provided'}), 400
                return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM keyboard_shortcuts 
            WHERE user_id = ? AND is_enabled = TRUE
            ORDER BY action_name
        ''', (user_id,))
        
        columns = [description[0] for description in cursor.description]
        shortcuts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
                return jsonify(shortcuts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DUPLICATE REMOVED: @advanced_ui_bp.route('/api/ui/keyboard-shortcuts', methods=['POST'])
# DUPLICATE REMOVED: def save_keyboard_shortcut():
    """Save or update keyboard shortcut"""
    try:
        data = request.get_json()
        
        required_fields = ['action_name', 'key_combination']
        for field in required_fields:
            if not data.get(field):
        return jsonify({'error': f'{field} is required'}), 400
        
        user_id = data.get('user_id', 'default')
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        # Check if shortcut exists
        cursor.execute('''
            SELECT id FROM keyboard_shortcuts 
            WHERE user_id = ? AND action_name = ?
        ''', (user_id, data['action_name']))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing shortcut
            cursor.execute('''
                UPDATE keyboard_shortcuts 
                SET key_combination = ?, description = ?, is_enabled = ?
                WHERE id = ?
            ''', (
                data['key_combination'],
                data.get('description', ''),
                data.get('is_enabled', True),
                existing[0]
            ))
        else:
            # Create new shortcut
            cursor.execute('''
                INSERT INTO keyboard_shortcuts (
                    user_id, action_name, key_combination, description, is_enabled, is_custom
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data['action_name'],
                data['key_combination'],
                data.get('description', ''),
                data.get('is_enabled', True),
                True
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Keyboard shortcut saved successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/activity/log', methods=['POST'])
def log_user_activity():
    """Log user activity"""
    try:
        data = request.get_json()
        
        if not data.get('action_type'):
        return jsonify({'error': 'action_type is required'}), 400
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_activity (
                user_id, action_type, action_target, action_details,
                ip_address, user_agent, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('user_id', 'default'),
            data['action_type'],
            data.get('action_target', ''),
            json.dumps(data.get('action_details', {})),
            request.remote_addr,
            request.headers.get('User-Agent', ''),
            data.get('session_id', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Activity logged successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/activity/stats')
def get_activity_stats():
    """Get user activity statistics"""
    try:
        user_id = request.args.get('user_id', 'default')
        days = int(request.args.get('days', 30))
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        # Activity by day
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM user_activity
            WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        '''.format(days), (user_id,))
        
        daily_activity = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Activity by type
        cursor.execute('''
            SELECT action_type, COUNT(*) as count
            FROM user_activity
            WHERE user_id = ? AND timestamp >= datetime('now', '-{} days')
            GROUP BY action_type
            ORDER BY count DESC
        '''.format(days), (user_id,))
        
        activity_by_type = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Most accessed content
        cursor.execute('''
            SELECT action_target, COUNT(*) as count
            FROM user_activity
            WHERE user_id = ? AND action_type = 'content_view' 
            AND timestamp >= datetime('now', '-{} days')
            AND action_target != ''
            GROUP BY action_target
            ORDER BY count DESC
            LIMIT 10
        '''.format(days), (user_id,))
        
        popular_content = [{'target': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'daily_activity': daily_activity,
            'activity_by_type': activity_by_type,
            'popular_content': popular_content,
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@advanced_ui_bp.route('/api/ui/components')
def get_ui_components():
    """Get available UI components"""
    try:
        component_type = request.args.get('type')
        
        conn = sqlite3.connect(UI_DB)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM ui_components WHERE is_enabled = TRUE'
        params = []
        
        if component_type:
            query += ' AND component_type = ?'
            params.append(component_type)
        
        query += ' ORDER BY sort_order, component_name'
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        components = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Parse JSON fields
        for component in components:
            for field in ['config_schema', 'default_config']:
                if component.get(field):
                    try:
                        component[field] = json.loads(component[field])
                    except:
                        component[field] = {}
        
        conn.close()
                        return jsonify(components)
        
    except Exception as e:
                        return jsonify({'error': str(e)}), 500

# Helper functions

def create_default_preferences(cursor, user_id, overrides=None):
    """Create default user preferences"""
    defaults = {
        'user_id': user_id,
        'theme_name': 'dark',
        'language': 'en',
        'timezone': 'UTC',
        'date_format': 'YYYY-MM-DD',
        'time_format': '24h',
        'grid_view_size': 'medium',
        'list_view_density': 'comfortable',
        'auto_play_trailers': False,
        'show_adult_content': False,
        'accessibility_mode': False,
        'high_contrast': False,
        'reduced_motion': False,
        'font_size': 'normal',
        'sidebar_collapsed': False,
        'dashboard_layout': json.dumps({
            'layout': 'grid',
            'widgets': ['recent_downloads', 'trending', 'recommendations', 'quick_actions']
        }),
        'quick_actions': json.dumps([
            'search', 'add_torrent', 'view_downloads', 'settings'
        ]),
        'notification_settings': json.dumps({
            'download_complete': True,
            'download_failed': True,
            'new_episodes': True,
            'system_updates': True,
            'sound_enabled': False,
            'desktop_notifications': True
        }),
        'keyboard_shortcuts': json.dumps({
            'search': 'Ctrl+K',
            'home': 'Ctrl+H',
            'downloads': 'Ctrl+D',
            'settings': 'Ctrl+,',
            'help': 'F1'
        }),
        'privacy_settings': json.dumps({
            'analytics_enabled': True,
            'crash_reporting': True,
            'usage_statistics': True
        })
    }
    
    if overrides:
        defaults.update(overrides)
        # Convert dict fields to JSON strings
        for field in ['dashboard_layout', 'quick_actions', 'notification_settings',
                     'keyboard_shortcuts', 'privacy_settings']:
            if field in defaults and isinstance(defaults[field], dict):
                defaults[field] = json.dumps(defaults[field])
    
    # Insert default preferences
    fields = list(defaults.keys())
    placeholders = ', '.join(['?' for _ in fields])
    values = [defaults[field] for field in fields]
    
    cursor.execute(f'''
        INSERT INTO user_preferences ({', '.join(fields)})
        VALUES ({placeholders})
    ''', values)
    
    return defaults

def create_default_themes():
    """Create default built-in themes"""
    conn = sqlite3.connect(UI_DB)
    cursor = conn.cursor()
    
    # Check if themes already exist
    cursor.execute('SELECT COUNT(*) FROM themes WHERE is_built_in = TRUE')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    themes = [
        {
            'name': 'dark',
            'display_name': 'Dark Theme',
            'description': 'Modern dark theme with blue accents',
            'author': 'MediaHub Team',
            'css_content': '''
                :root {
                    --primary-bg: #1a1a1a;
                    --secondary-bg: #2d2d2d;
                    --accent-color: #3b82f6;
                    --text-primary: #ffffff;
                    --text-secondary: #a1a1aa;
                    --border-color: #404040;
                }
                
                body {
                    background-color: var(--primary-bg);
                    color: var(--text-primary);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .card {
                    background-color: var(--secondary-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 1rem;
                }
                
                .btn-primary {
                    background-color: var(--accent-color);
                    border-color: var(--accent-color);
                }
            ''',
            'is_built_in': True,
            'is_active': True
        },
        {
            'name': 'light',
            'display_name': 'Light Theme',
            'description': 'Clean light theme for daytime use',
            'author': 'MediaHub Team',
            'css_content': '''
                :root {
                    --primary-bg: #ffffff;
                    --secondary-bg: #f8fafc;
                    --accent-color: #3b82f6;
                    --text-primary: #1f2937;
                    --text-secondary: #6b7280;
                    --border-color: #e5e7eb;
                }
                
                body {
                    background-color: var(--primary-bg);
                    color: var(--text-primary);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }
                
                .card {
                    background-color: var(--secondary-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 1rem;
                }
                
                .btn-primary {
                    background-color: var(--accent-color);
                    border-color: var(--accent-color);
                }
            ''',
            'is_built_in': True,
            'is_active': False
        },
        {
            'name': 'high_contrast',
            'display_name': 'High Contrast',
            'description': 'High contrast theme for accessibility',
            'author': 'MediaHub Team',
            'css_content': '''
                :root {
                    --primary-bg: #000000;
                    --secondary-bg: #1a1a1a;
                    --accent-color: #ffff00;
                    --text-primary: #ffffff;
                    --text-secondary: #ffffff;
                    --border-color: #ffffff;
                }
                
                body {
                    background-color: var(--primary-bg);
                    color: var(--text-primary);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    font-weight: bold;
                }
                
                .card {
                    background-color: var(--secondary-bg);
                    border: 2px solid var(--border-color);
                    border-radius: 4px;
                    padding: 1rem;
                }
                
                .btn-primary {
                    background-color: var(--accent-color);
                    color: #000000;
                    border: 2px solid var(--accent-color);
                    font-weight: bold;
                }
                
                a {
                    color: var(--accent-color);
                    text-decoration: underline;
                }
            ''',
            'is_built_in': True,
            'is_active': False
        }
    ]
    
    for theme in themes:
        cursor.execute('''
            INSERT INTO themes (
                name, display_name, description, author, css_content, 
                is_built_in, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            theme['name'], theme['display_name'], theme['description'],
            theme['author'], theme['css_content'], theme['is_built_in'],
            theme['is_active']
        ))
    
    conn.commit()
    conn.close()

def create_default_keyboard_shortcuts():
    """Create default keyboard shortcuts"""
    conn = sqlite3.connect(UI_DB)
    cursor = conn.cursor()
    
    # Check if shortcuts already exist
    cursor.execute('SELECT COUNT(*) FROM keyboard_shortcuts WHERE is_custom = FALSE')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    shortcuts = [
        {'action_name': 'search', 'key_combination': 'Ctrl+K', 'description': 'Open search'},
        {'action_name': 'home', 'key_combination': 'Ctrl+H', 'description': 'Go to home'},
        {'action_name': 'downloads', 'key_combination': 'Ctrl+D', 'description': 'View downloads'},
        {'action_name': 'settings', 'key_combination': 'Ctrl+,', 'description': 'Open settings'},
        {'action_name': 'help', 'key_combination': 'F1', 'description': 'Show help'},
        {'action_name': 'refresh', 'key_combination': 'F5', 'description': 'Refresh page'},
        {'action_name': 'fullscreen', 'key_combination': 'F11', 'description': 'Toggle fullscreen'},
        {'action_name': 'escape', 'key_combination': 'Escape', 'description': 'Close modal/cancel'},
    ]
    
    for shortcut in shortcuts:
        cursor.execute('''
            INSERT INTO keyboard_shortcuts (
                user_id, action_name, key_combination, description, is_custom
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            'default', shortcut['action_name'], shortcut['key_combination'],
            shortcut['description'], False
        ))
    
    conn.commit()
    conn.close()

# Initialize default data
create_default_themes()
create_default_keyboard_shortcuts()
