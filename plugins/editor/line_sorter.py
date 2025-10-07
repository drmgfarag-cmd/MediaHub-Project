"""
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
        
        lines = text.split('\n')
        reverse = options.get('reverse', False)
        numeric = options.get('numeric', False)
        
        if numeric:
            try:
                lines = sorted(lines, key=lambda x: float(x) if x.strip() else 0, reverse=reverse)
            except ValueError:
                lines = sorted(lines, reverse=reverse)
        else:
            lines = sorted(lines, reverse=reverse)
        
        return '\n'.join(lines)

    def get_menu_items(self):
        return [
            {'label': 'Sort A-Z', 'action': 'transform', 'options': {'reverse': False}},
            {'label': 'Sort Z-A', 'action': 'transform', 'options': {'reverse': True}},
            {'label': 'Sort Numeric', 'action': 'transform', 'options': {'numeric': True}}
        ]
