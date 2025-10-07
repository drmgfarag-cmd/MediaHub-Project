"""
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
