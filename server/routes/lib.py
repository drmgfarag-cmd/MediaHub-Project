"""
Library utilities for routes
"""
import os
import sqlite3
from pathlib import Path

def get_db_connection():
    """Get database connection"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'mediahub.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    """Query the database"""
    conn = get_db_connection()
    cur = conn.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Execute a database command"""
    conn = get_db_connection()
    conn.execute(query, args)
    conn.commit()
    conn.close()
