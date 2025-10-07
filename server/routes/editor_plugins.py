"""
Plugin System for MediaHub Text Editor
Provides extensibility through Python-based plugins
"""

from flask import Blueprint, request, jsonify
import os
import importlib.util
import inspect
from pathlib import Path

editor_plugins_bp = Blueprint('editor_plugins', __name__)

# Plugin directory
PLUGINS_DIR = Path(__file__).parent.parent.parent / 'plugins' / 'editor'
PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

# Loaded plugins cache
loaded_plugins = {}


class EditorPlugin:
    """
    Base class for editor plugins
    """
    def __init__(self):
        self.name = "Unnamed Plugin"
        self.version = "1.0.0"
        self.description = "No description"
        self.author = "Unknown"
        self.enabled = True

    def transform_text(self, text, options=None):
        """
        Transform text content
        Args:
            text: Input text
            options: Optional parameters
        Returns:
            Transformed text
        """
        return text

    def get_menu_items(self):
        """
        Return menu items for this plugin
        Returns:
            List of menu item dictionaries
        """
        return []

    def on_enable(self):
        """Called when plugin is enabled"""
        pass

    def on_disable(self):
        """Called when plugin is disabled"""
        pass


def discover_plugins():
    """
    Discover all available plugins
    """
    plugins = []
    
    if not PLUGINS_DIR.exists():
        return plugins

    for file_path in PLUGINS_DIR.glob('*.py'):
        if file_path.name.startswith('_'):
            continue

        try:
            # Load module
            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, EditorPlugin) and 
                    obj != EditorPlugin):
                    
                    plugins.append({
                        'id': file_path.stem,
                        'name': name,
                        'file': str(file_path),
                        'class': obj
                    })

        except Exception as e:
            print(f"Error loading plugin {file_path}: {e}")

    return plugins


def load_plugin(plugin_id):
    """
    Load a specific plugin
    """
    if plugin_id in loaded_plugins:
        return loaded_plugins[plugin_id]

    plugins = discover_plugins()
    for plugin_info in plugins:
        if plugin_info['id'] == plugin_id:
            try:
                instance = plugin_info['class']()
                loaded_plugins[plugin_id] = instance
                instance.on_enable()
                return instance
            except Exception as e:
                print(f"Error instantiating plugin {plugin_id}: {e}")
                return None

    return None


@editor_plugins_bp.route('/api/editor/plugins/list', methods=['GET'])
def list_plugins():
    """
    List all available plugins
    """
    try:
        plugins = discover_plugins()
        
        plugin_list = []
        for plugin_info in plugins:
            try:
                instance = plugin_info['class']()
                plugin_list.append({
                    'id': plugin_info['id'],
                    'name': instance.name,
                    'version': instance.version,
                    'description': instance.description,
                    'author': instance.author,
                    'enabled': plugin_info['id'] in loaded_plugins,
                    'file': plugin_info['file']
                })
            except Exception as e:
                print(f"Error getting plugin info: {e}")

        return jsonify({
            'success': True,
            'plugins': plugin_list,
            'total': len(plugin_list)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@editor_plugins_bp.route('/api/editor/plugins/<plugin_id>/enable', methods=['POST'])
def enable_plugin(plugin_id):
    """
    Enable a plugin
    """
    try:
        plugin = load_plugin(plugin_id)
        if not plugin:
            return jsonify({'error': 'Plugin not found'}), 404

        return jsonify({
            'success': True,
            'message': f'Plugin {plugin.name} enabled'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@editor_plugins_bp.route('/api/editor/plugins/<plugin_id>/disable', methods=['POST'])
def disable_plugin(plugin_id):
    """
    Disable a plugin
    """
    try:
        if plugin_id in loaded_plugins:
            plugin = loaded_plugins[plugin_id]
            plugin.on_disable()
            del loaded_plugins[plugin_id]

        return jsonify({
            'success': True,
            'message': 'Plugin disabled'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@editor_plugins_bp.route('/api/editor/plugins/<plugin_id>/execute', methods=['POST'])
def execute_plugin(plugin_id):
    """
    Execute a plugin transformation
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        options = data.get('options', {})

        plugin = load_plugin(plugin_id)
        if not plugin:
            return jsonify({'error': 'Plugin not found'}), 404

        if not plugin.enabled:
            return jsonify({'error': 'Plugin is disabled'}), 400

        result = plugin.transform_text(text, options)

        return jsonify({
            'success': True,
            'result': result
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@editor_plugins_bp.route('/api/editor/plugins/<plugin_id>/info', methods=['GET'])
def get_plugin_info(plugin_id):
    """
    Get detailed plugin information
    """
    try:
        plugin = load_plugin(plugin_id)
        if not plugin:
            return jsonify({'error': 'Plugin not found'}), 404

        return jsonify({
            'success': True,
            'plugin': {
                'id': plugin_id,
                'name': plugin.name,
                'version': plugin.version,
                'description': plugin.description,
                'author': plugin.author,
                'enabled': plugin.enabled,
                'menu_items': plugin.get_menu_items()
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Create sample plugins
def create_sample_plugins():
    """
    Create sample plugins for demonstration
    """
    # Sample plugin 1: Case converter
    case_converter = '''"""
Case Converter Plugin
Converts text case (upper, lower, title, sentence)
"""

from server.routes.editor_plugins import EditorPlugin


class CaseConverterPlugin(EditorPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Case Converter"
        self.version = "1.0.0"
        self.description = "Convert text case (upper, lower, title, sentence)"
        self.author = "MediaHub"

    def transform_text(self, text, options=None):
        if not options:
            options = {}
        
        case_type = options.get('case_type', 'upper')
        
        if case_type == 'upper':
            return text.upper()
        elif case_type == 'lower':
            return text.lower()
        elif case_type == 'title':
            return text.title()
        elif case_type == 'sentence':
            return '. '.join(s.capitalize() for s in text.split('. '))
        else:
            return text

    def get_menu_items(self):
        return [
            {'label': 'UPPERCASE', 'action': 'transform', 'options': {'case_type': 'upper'}},
            {'label': 'lowercase', 'action': 'transform', 'options': {'case_type': 'lower'}},
            {'label': 'Title Case', 'action': 'transform', 'options': {'case_type': 'title'}},
            {'label': 'Sentence case', 'action': 'transform', 'options': {'case_type': 'sentence'}}
        ]
'''

    # Sample plugin 2: Line sorter
    line_sorter = '''"""
Line Sorter Plugin
Sorts lines alphabetically or numerically
"""

from server.routes.editor_plugins import EditorPlugin


class LineSorterPlugin(EditorPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Line Sorter"
        self.version = "1.0.0"
        self.description = "Sort lines alphabetically or numerically"
        self.author = "MediaHub"

    def transform_text(self, text, options=None):
        if not options:
            options = {}
        
        lines = text.split('\\n')
        reverse = options.get('reverse', False)
        numeric = options.get('numeric', False)
        
        if numeric:
            try:
                lines = sorted(lines, key=lambda x: float(x) if x.strip() else 0, reverse=reverse)
            except ValueError:
                lines = sorted(lines, reverse=reverse)
        else:
            lines = sorted(lines, reverse=reverse)
        
        return '\\n'.join(lines)

    def get_menu_items(self):
        return [
            {'label': 'Sort A-Z', 'action': 'transform', 'options': {'reverse': False}},
            {'label': 'Sort Z-A', 'action': 'transform', 'options': {'reverse': True}},
            {'label': 'Sort Numeric', 'action': 'transform', 'options': {'numeric': True}}
        ]
'''

    # Write sample plugins
    (PLUGINS_DIR / 'case_converter.py').write_text(case_converter)
    (PLUGINS_DIR / 'line_sorter.py').write_text(line_sorter)


# Create sample plugins on module load
try:
    create_sample_plugins()
except Exception as e:
    print(f"Error creating sample plugins: {e}")
