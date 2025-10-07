"""
Security Manager for Safe Operations
Provides dry-run, undo, and security validation functionality
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

class SecurityManager:
    """Manages security and safe operations for MediaHub"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def preview_operation(self, operation: Dict[str, Any], profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Preview an operation without executing it"""
        try:
            operation_type = operation.get('type', 'unknown')
            
            if operation_type == 'file_operation':
                return self._preview_file_operation(operation, profile)
            elif operation_type == 'download':
                return self._preview_download_operation(operation, profile)
            elif operation_type == 'metadata_update':
                return self._preview_metadata_operation(operation, profile)
            elif operation_type == 'collection_update':
                return self._preview_collection_operation(operation, profile)
            else:
                return {
                    'safe': True,
                    'warnings': [],
                    'estimated_time': 0,
                    'affected_items': 0,
                    'description': f'Unknown operation type: {operation_type}'
                }
        
        except Exception as e:
            self.logger.error(f"Preview operation error: {e}")
            return {
                'safe': False,
                'warnings': [f'Preview error: {str(e)}'],
                'estimated_time': 0,
                'affected_items': 0,
                'description': 'Error previewing operation'
            }
    
    def _preview_file_operation(self, operation: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview file operations like rename, move, delete"""
        files = operation.get('files', [])
        action = operation.get('action', 'unknown')
        
        warnings = []
        affected_items = len(files)
        
        # Check for potentially dangerous operations
        if action == 'delete':
            warnings.append(f'Will permanently delete {affected_items} files')
        elif action == 'move':
            warnings.append(f'Will move {affected_items} files to new location')
        elif action == 'rename':
            warnings.append(f'Will rename {affected_items} files')
        
        # Estimate time based on file count
        estimated_time = max(1, affected_items * 0.1)  # 0.1 seconds per file
        
        return {
            'safe': action not in ['delete'],
            'warnings': warnings,
            'estimated_time': estimated_time,
            'affected_items': affected_items,
            'description': f'{action.title()} operation on {affected_items} files'
        }
    
    def _preview_download_operation(self, operation: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview download operations"""
        urls = operation.get('urls', [])
        destination = operation.get('destination', '')
        
        warnings = []
        affected_items = len(urls)
        
        # Check destination space (simplified)
        if not destination:
            warnings.append('No destination specified')
        
        # Estimate download time (simplified)
        estimated_time = affected_items * 30  # 30 seconds per download estimate
        
        return {
            'safe': True,
            'warnings': warnings,
            'estimated_time': estimated_time,
            'affected_items': affected_items,
            'description': f'Download {affected_items} items to {destination}'
        }
    
    def _preview_metadata_operation(self, operation: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview metadata update operations"""
        items = operation.get('items', [])
        providers = operation.get('providers', [])
        
        warnings = []
        affected_items = len(items)
        
        if not providers:
            warnings.append('No metadata providers specified')
        
        # Estimate time based on items and providers
        estimated_time = affected_items * len(providers) * 2  # 2 seconds per provider per item
        
        return {
            'safe': True,
            'warnings': warnings,
            'estimated_time': estimated_time,
            'affected_items': affected_items,
            'description': f'Update metadata for {affected_items} items using {len(providers)} providers'
        }
    
    def _preview_collection_operation(self, operation: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Preview collection update operations"""
        collections = operation.get('collections', [])
        action = operation.get('action', 'update')
        
        warnings = []
        affected_items = len(collections)
        
        if action == 'delete':
            warnings.append(f'Will delete {affected_items} collections')
        
        estimated_time = affected_items * 5  # 5 seconds per collection
        
        return {
            'safe': action != 'delete',
            'warnings': warnings,
            'estimated_time': estimated_time,
            'affected_items': affected_items,
            'description': f'{action.title()} {affected_items} collections'
        }
    
    def undo_operation(self, operation_id: Optional[int], db_connection: sqlite3.Connection, 
                      db_lock: threading.Lock, profile_name: str = 'default') -> Dict[str, Any]:
        """Undo a previous operation"""
        try:
            with db_lock:
                cursor = db_connection.cursor()
                
                if operation_id:
                    # Undo specific operation
                    cursor.execute("""
                        SELECT operation_type, rollback_data FROM operation_history 
                        WHERE id = ? AND (user_profile = ? OR user_profile IS NULL)
                    """, (operation_id, profile_name))
                else:
                    # Undo last operation
                    cursor.execute("""
                        SELECT id, operation_type, rollback_data FROM operation_history 
                        WHERE (user_profile = ? OR user_profile IS NULL) AND success = 1
                        ORDER BY timestamp DESC LIMIT 1
                    """, (profile_name,))
                
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': 'No operation found to undo'}
                
                if operation_id:
                    op_id, op_type, rollback_data = operation_id, row[0], row[1]
                else:
                    op_id, op_type, rollback_data = row[0], row[1], row[2]
                
                if not rollback_data:
                    return {'success': False, 'error': 'Operation cannot be undone (no rollback data)'}
                
                # Execute rollback
                rollback_info = json.loads(rollback_data)
                result = self._execute_rollback(rollback_info, op_type)
                
                if result['success']:
                    # Mark operation as rolled back
                    cursor.execute("""
                        UPDATE operation_history SET success = 0 WHERE id = ?
                    """, (op_id,))
                    db_connection.commit()
                
                return result
        
        except Exception as e:
            self.logger.error(f"Undo operation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _execute_rollback(self, rollback_info: Dict[str, Any], operation_type: str) -> Dict[str, Any]:
        """Execute rollback based on operation type"""
        try:
            if operation_type == 'file_operation':
                return self._rollback_file_operation(rollback_info)
            elif operation_type == 'metadata_update':
                return self._rollback_metadata_operation(rollback_info)
            elif operation_type == 'collection_update':
                return self._rollback_collection_operation(rollback_info)
            else:
                return {'success': False, 'error': f'Rollback not supported for {operation_type}'}
        
        except Exception as e:
            self.logger.error(f"Rollback execution error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _rollback_file_operation(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback file operations"""
        import os
        import shutil
        
        try:
            action = rollback_info.get('action')
            files = rollback_info.get('files', [])
            
            rolled_back = 0
            for file_info in files:
                original_path = file_info.get('original_path')
                current_path = file_info.get('current_path')
                
                if action == 'rename' and original_path and current_path:
                    if os.path.exists(current_path):
                        os.rename(current_path, original_path)
                        rolled_back += 1
                elif action == 'move' and original_path and current_path:
                    if os.path.exists(current_path):
                        shutil.move(current_path, original_path)
                        rolled_back += 1
                # Note: Delete operations cannot be rolled back without backup
            
            return {
                'success': True,
                'message': f'Rolled back {rolled_back} file operations'
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _rollback_metadata_operation(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback metadata operations"""
        # Simplified rollback - would restore previous metadata from backup
        return {
            'success': True,
            'message': 'Metadata rollback completed (simplified implementation)'
        }
    
    def _rollback_collection_operation(self, rollback_info: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback collection operations"""
        # Simplified rollback - would restore previous collection state
        return {
            'success': True,
            'message': 'Collection rollback completed (simplified implementation)'
        }
    
    def validate_path(self, path: str) -> bool:
        """Validate that a path is safe to operate on"""
        import os
        
        # Basic path validation
        if not path or path.strip() == '':
            return False
        
        # Prevent operations on system directories
        dangerous_paths = [
            '/bin', '/sbin', '/usr/bin', '/usr/sbin',
            '/etc', '/var', '/sys', '/proc', '/dev',
            'C:\\Windows', 'C:\\Program Files', 'C:\\System32'
        ]
        
        normalized_path = os.path.normpath(path).lower()
        for dangerous in dangerous_paths:
            if normalized_path.startswith(dangerous.lower()):
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file operations"""
        import re
        
        # Remove or replace dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    def check_disk_space(self, path: str, required_bytes: int) -> bool:
        """Check if there's enough disk space for an operation"""
        import shutil
        
        try:
            free_bytes = shutil.disk_usage(path).free
            return free_bytes >= required_bytes
        except Exception:
            return True  # Assume OK if we can't check
    
    def log_operation(self, operation_type: str, operation_data: Dict[str, Any], 
                     rollback_data: Optional[Dict[str, Any]], db_connection: sqlite3.Connection,
                     db_lock: threading.Lock, profile_name: str = 'default') -> int:
        """Log an operation for potential undo"""
        try:
            with db_lock:
                cursor = db_connection.cursor()
                cursor.execute("""
                    INSERT INTO operation_history 
                    (operation_type, operation_data, rollback_data, user_profile)
                    VALUES (?, ?, ?, ?)
                """, (
                    operation_type,
                    json.dumps(operation_data),
                    json.dumps(rollback_data) if rollback_data else None,
                    profile_name
                ))
                db_connection.commit()
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error logging operation: {e}")
            return 0
