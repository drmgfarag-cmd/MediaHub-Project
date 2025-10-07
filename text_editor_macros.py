#!/usr/bin/env python3
"""
Text Editor Macro System
Advanced macro recording and playback for the MediaHub Ultimate Text Editor
"""

import json
import time
from typing import List, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QTextEdit, QMessageBox, QInputDialog
)

class MacroAction:
    """Represents a single macro action"""
    
    def __init__(self, action_type: str, data: Dict[str, Any], timestamp: float = None):
        self.action_type = action_type
        self.data = data
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type,
            'data': self.data,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroAction':
        return cls(
            data['action_type'],
            data['data'],
            data.get('timestamp', time.time())
        )

class Macro:
    """Represents a complete macro sequence"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.actions: List[MacroAction] = []
        self.created_at = time.time()
    
    def add_action(self, action: MacroAction):
        """Add an action to the macro"""
        self.actions.append(action)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'actions': [action.to_dict() for action in self.actions],
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Macro':
        macro = cls(data['name'], data.get('description', ''))
        macro.actions = [MacroAction.from_dict(action_data) for action_data in data.get('actions', [])]
        macro.created_at = data.get('created_at', time.time())
        return macro

class MacroRecorder(QObject):
    """Records and manages macros"""
    
    macro_recorded = pyqtSignal(Macro)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.current_macro: Macro = None
        self.macros: Dict[str, Macro] = {}
        self.start_time = 0
    
    def start_recording(self, name: str, description: str = ""):
        """Start recording a new macro"""
        if self.is_recording:
            return False
        
        self.current_macro = Macro(name, description)
        self.is_recording = True
        self.start_time = time.time()
        return True
    
    def stop_recording(self):
        """Stop recording and save the macro"""
        if not self.is_recording or not self.current_macro:
            return None
        
        self.is_recording = False
        macro = self.current_macro
        self.macros[macro.name] = macro
        self.macro_recorded.emit(macro)
        self.current_macro = None
        return macro
    
    def record_action(self, action_type: str, data: Dict[str, Any]):
        """Record a single action"""
        if not self.is_recording or not self.current_macro:
            return
        
        action = MacroAction(action_type, data)
        self.current_macro.add_action(action)
    
    def get_macro(self, name: str) -> Macro:
        """Get a macro by name"""
        return self.macros.get(name)
    
    def delete_macro(self, name: str) -> bool:
        """Delete a macro"""
        if name in self.macros:
            del self.macros[name]
            return True
        return False
    
    def save_macros(self, filepath: str):
        """Save all macros to file"""
        data = {
            'macros': {name: macro.to_dict() for name, macro in self.macros.items()}
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_macros(self, filepath: str):
        """Load macros from file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.macros = {}
            for name, macro_data in data.get('macros', {}).items():
                self.macros[name] = Macro.from_dict(macro_data)
        except Exception as e:
            print(f"Error loading macros: {e}")

class MacroPlayer(QObject):
    """Plays back recorded macros"""
    
    playback_started = pyqtSignal()
    playback_finished = pyqtSignal()
    action_executed = pyqtSignal(str, dict)
    
    def __init__(self, editor_bridge):
        super().__init__()
        self.editor_bridge = editor_bridge
        self.is_playing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._execute_next_action)
        self.current_macro = None
        self.action_index = 0
        self.playback_speed = 1.0  # 1.0 = normal speed
    
    def play_macro(self, macro: Macro, speed: float = 1.0):
        """Play a macro"""
        if self.is_playing:
            return False
        
        self.current_macro = macro
        self.action_index = 0
        self.playback_speed = max(0.1, min(10.0, speed))  # Clamp speed
        self.is_playing = True
        self.playback_started.emit()
        
        if macro.actions:
            self._execute_next_action()
        else:
            self._finish_playback()
        
        return True
    
    def stop_playback(self):
        """Stop macro playback"""
        if self.is_playing:
            self.timer.stop()
            self.is_playing = False
            self.playback_finished.emit()
    
    def _execute_next_action(self):
        """Execute the next action in the macro"""
        if not self.is_playing or not self.current_macro:
            return
        
        if self.action_index >= len(self.current_macro.actions):
            self._finish_playback()
            return
        
        action = self.current_macro.actions[self.action_index]
        self._execute_action(action)
        
        self.action_index += 1
        
        # Schedule next action
        if self.action_index < len(self.current_macro.actions):
            next_action = self.current_macro.actions[self.action_index]
            delay = self._calculate_delay(action, next_action)
            self.timer.start(int(delay / self.playback_speed))
        else:
            self._finish_playback()
    
    def _execute_action(self, action: MacroAction):
        """Execute a single action"""
        try:
            if action.action_type == 'type_text':
                text = action.data.get('text', '')
                self.editor_bridge.insert_text(text)
            
            elif action.action_type == 'key_combination':
                # Handle key combinations like Ctrl+C, Ctrl+V, etc.
                combo = action.data.get('combination', '')
                self._execute_key_combination(combo)
            
            elif action.action_type == 'cursor_move':
                line = action.data.get('line', 1)
                column = action.data.get('column', 1)
                self.editor_bridge.set_cursor_position(line, column)
            
            elif action.action_type == 'selection':
                start_line = action.data.get('start_line', 1)
                start_column = action.data.get('start_column', 1)
                end_line = action.data.get('end_line', 1)
                end_column = action.data.get('end_column', 1)
                self.editor_bridge.set_selection(start_line, start_column, end_line, end_column)
            
            elif action.action_type == 'command':
                command = action.data.get('command', '')
                self._execute_command(command)
            
            self.action_executed.emit(action.action_type, action.data)
        
        except Exception as e:
            print(f"Error executing action {action.action_type}: {e}")
    
    def _execute_key_combination(self, combination: str):
        """Execute key combinations"""
        if combination == 'Ctrl+C':
            self.editor_bridge.copy()
        elif combination == 'Ctrl+V':
            self.editor_bridge.paste()
        elif combination == 'Ctrl+X':
            self.editor_bridge.cut()
        elif combination == 'Ctrl+Z':
            self.editor_bridge.undo()
        elif combination == 'Ctrl+Y':
            self.editor_bridge.redo()
        # Add more key combinations as needed
    
    def _execute_command(self, command: str):
        """Execute editor commands"""
        if command == 'find':
            self.editor_bridge.show_find_dialog()
        elif command == 'replace':
            self.editor_bridge.show_replace_dialog()
        elif command == 'goto_line':
            self.editor_bridge.show_goto_line_dialog()
        # Add more commands as needed
    
    def _calculate_delay(self, current_action: MacroAction, next_action: MacroAction) -> int:
        """Calculate delay between actions in milliseconds"""
        if next_action.timestamp and current_action.timestamp:
            delay = (next_action.timestamp - current_action.timestamp) * 1000
            return max(50, min(5000, delay))  # Clamp between 50ms and 5s
        return 100  # Default delay
    
    def _finish_playback(self):
        """Finish macro playback"""
        self.timer.stop()
        self.is_playing = False
        self.current_macro = None
        self.action_index = 0
        self.playback_finished.emit()

class MacroManagerDialog(QDialog):
    """Dialog for managing macros"""
    
    def __init__(self, macro_recorder: MacroRecorder, parent=None):
        super().__init__(parent)
        self.macro_recorder = macro_recorder
        self.setWindowTitle("Macro Manager")
        self.setModal(True)
        self.resize(600, 400)
        self.setup_ui()
        self.refresh_macro_list()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Macro list
        self.macro_list = QListWidget()
        self.macro_list.currentItemChanged.connect(self.on_macro_selected)
        layout.addWidget(QLabel("Saved Macros:"))
        layout.addWidget(self.macro_list)
        
        # Macro details
        details_layout = QVBoxLayout()
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        
        details_layout.addWidget(QLabel("Name:"))
        details_layout.addWidget(self.name_edit)
        details_layout.addWidget(QLabel("Description:"))
        details_layout.addWidget(self.description_edit)
        
        layout.addLayout(details_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("Record New")
        self.record_btn.clicked.connect(self.record_new_macro)
        
        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.clicked.connect(self.stop_recording)
        self.stop_btn.setEnabled(False)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_selected_macro)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected_macro)
        
        self.save_btn = QPushButton("Save to File")
        self.save_btn.clicked.connect(self.save_macros)
        
        self.load_btn = QPushButton("Load from File")
        self.load_btn.clicked.connect(self.load_macros)
        
        button_layout.addWidget(self.record_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.load_btn)
        
        layout.addLayout(button_layout)
        
        # Connect recorder signals
        self.macro_recorder.macro_recorded.connect(self.on_macro_recorded)
    
    def refresh_macro_list(self):
        """Refresh the macro list"""
        self.macro_list.clear()
        for name, macro in self.macro_recorder.macros.items():
            item = QListWidgetItem(f"{name} ({len(macro.actions)} actions)")
            item.setData(32, name)  # Store macro name
            self.macro_list.addItem(item)
    
    def on_macro_selected(self, current, previous):
        """Handle macro selection"""
        if current:
            macro_name = current.data(32)
            macro = self.macro_recorder.get_macro(macro_name)
            if macro:
                self.name_edit.setText(macro.name)
                self.description_edit.setText(macro.description)
    
    def record_new_macro(self):
        """Start recording a new macro"""
        name, ok = QInputDialog.getText(self, "New Macro", "Macro name:")
        if ok and name:
            description, _ = QInputDialog.getText(self, "New Macro", "Description (optional):")
            if self.macro_recorder.start_recording(name, description):
                self.record_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                QMessageBox.information(self, "Recording", f"Recording macro '{name}'. Perform your actions then click 'Stop Recording'.")
    
    def stop_recording(self):
        """Stop recording the current macro"""
        macro = self.macro_recorder.stop_recording()
        if macro:
            self.record_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            QMessageBox.information(self, "Recording Complete", f"Macro '{macro.name}' recorded with {len(macro.actions)} actions.")
            self.refresh_macro_list()
    
    def play_selected_macro(self):
        """Play the selected macro"""
        current_item = self.macro_list.currentItem()
        if current_item:
            macro_name = current_item.data(32)
            macro = self.macro_recorder.get_macro(macro_name)
            if macro:
                QMessageBox.information(self, "Playing Macro", f"Playing macro '{macro.name}' with {len(macro.actions)} actions.")
                # Note: Actual playback would need to be implemented in the main editor
    
    def delete_selected_macro(self):
        """Delete the selected macro"""
        current_item = self.macro_list.currentItem()
        if current_item:
            macro_name = current_item.data(32)
            reply = QMessageBox.question(self, "Delete Macro", f"Delete macro '{macro_name}'?")
            if reply == QMessageBox.StandardButton.Yes:
                self.macro_recorder.delete_macro(macro_name)
                self.refresh_macro_list()
    
    def save_macros(self):
        """Save macros to file"""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Macros", "macros.json", "JSON Files (*.json)")
        if filepath:
            self.macro_recorder.save_macros(filepath)
            QMessageBox.information(self, "Saved", f"Macros saved to {filepath}")
    
    def load_macros(self):
        """Load macros from file"""
        from PyQt6.QtWidgets import QFileDialog
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Macros", "", "JSON Files (*.json)")
        if filepath:
            self.macro_recorder.load_macros(filepath)
            self.refresh_macro_list()
            QMessageBox.information(self, "Loaded", f"Macros loaded from {filepath}")
    
    def on_macro_recorded(self, macro: Macro):
        """Handle when a macro is recorded"""
        self.refresh_macro_list()
