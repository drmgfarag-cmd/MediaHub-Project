"""
Logging Configuration for MediaHub
Provides comprehensive logging with security-aware redaction
"""

import logging
import logging.handlers
import os
import re
from pathlib import Path
from typing import Any

def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Setup comprehensive logging system with security redaction"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger('mediahub')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = SecurityRedactingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    simple_formatter = SecurityRedactingFormatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'mediahub.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'mediahub_errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    return logger

class SecurityRedactingFormatter(logging.Formatter):
    """Formatter that redacts sensitive information from logs"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Patterns for sensitive data redaction
        self.redaction_patterns = [
            # API Keys
            (re.compile(r'(api[_-]?key["\s]*[:=]["\s]*)([a-zA-Z0-9]{20,})(["\s]*)', re.IGNORECASE), r'\1***REDACTED***\3'),
            (re.compile(r'(token["\s]*[:=]["\s]*)([a-zA-Z0-9]{20,})(["\s]*)', re.IGNORECASE), r'\1***REDACTED***\3'),
            (re.compile(r'(bearer["\s]+)([a-zA-Z0-9]{20,})(["\s]*)', re.IGNORECASE), r'\1***REDACTED***\3'),
            
            # Real-Debrid specific
            (re.compile(r'(HMPNSB7QFO4RL2D[A-Z0-9]+)', re.IGNORECASE), r'***RD-KEY-REDACTED***'),
            
            # TMDB API Key
            (re.compile(r'(3aca2154c1d9223036904a86202897ba)', re.IGNORECASE), r'***TMDB-KEY-REDACTED***'),
            
            # Google API Key
            (re.compile(r'(AIzaSy[a-zA-Z0-9_-]{33})', re.IGNORECASE), r'***GOOGLE-KEY-REDACTED***'),
            
            # Generic long alphanumeric strings that might be keys
            (re.compile(r'(["\s=:])([a-zA-Z0-9]{32,})(["\s,}])', re.IGNORECASE), r'\1***KEY-REDACTED***\3'),
            
            # Passwords
            (re.compile(r'(password["\s]*[:=]["\s]*)([^"\s,}]+)(["\s,}]*)', re.IGNORECASE), r'\1***REDACTED***\3'),
            (re.compile(r'(pass["\s]*[:=]["\s]*)([^"\s,}]+)(["\s,}]*)', re.IGNORECASE), r'\1***REDACTED***\3'),
            
            # URLs with credentials
            (re.compile(r'(https?://[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***REDACTED***\3'),
            
            # File paths (partial redaction)
            (re.compile(r'(/home/[^/\s]+)', re.IGNORECASE), r'/home/***'),
            (re.compile(r'(C:\\Users\\[^\\]+)', re.IGNORECASE), r'C:\\Users\\***'),
        ]
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with security redaction"""
        # Format the message normally first
        formatted = super().format(record)
        
        # Apply redaction patterns
        for pattern, replacement in self.redaction_patterns:
            formatted = pattern.sub(replacement, formatted)
        
        return formatted
    
    def redact_message(self, message: str) -> str:
        """Redact sensitive information from a message"""
        for pattern, replacement in self.redaction_patterns:
            message = pattern.sub(replacement, message)
        return message

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module"""
    return logging.getLogger(f'mediahub.{name}')

def log_api_call(logger: logging.Logger, service: str, endpoint: str, 
                response_code: int, response_time: float):
    """Log API calls with consistent format"""
    logger.info(f"API Call - Service: {service}, Endpoint: {endpoint}, "
               f"Status: {response_code}, Time: {response_time:.2f}s")

def log_operation(logger: logging.Logger, operation: str, details: dict, 
                 success: bool = True, duration: float = 0):
    """Log operations with consistent format"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"Operation {status} - {operation} - Duration: {duration:.2f}s - Details: {details}")

def log_security_event(logger: logging.Logger, event_type: str, details: dict, 
                      severity: str = 'INFO'):
    """Log security events with special handling"""
    level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(level, f"SECURITY EVENT - {event_type} - {details}")

def log_user_action(logger: logging.Logger, user: str, action: str, 
                   resource: str, success: bool = True):
    """Log user actions for audit trail"""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"USER ACTION {status} - User: {user}, Action: {action}, Resource: {resource}")

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Operation completed: {self.operation} - Duration: {duration:.2f}s")
        else:
            self.logger.error(f"Operation failed: {self.operation} - Duration: {duration:.2f}s - Error: {exc_val}")

def setup_request_logging(app):
    """Setup request logging for Flask app"""
    
    @app.before_request
    def log_request_info():
        from flask import request
        logger = get_logger('requests')
        logger.debug(f"Request: {request.method} {request.url} - IP: {request.remote_addr}")
    
    @app.after_request
    def log_response_info(response):
        from flask import request
        logger = get_logger('requests')
        logger.debug(f"Response: {request.method} {request.url} - Status: {response.status_code}")
        return response
