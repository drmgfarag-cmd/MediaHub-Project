from flask import Blueprint, jsonify, request, make_response
import os, json, secrets, time

security_bp = Blueprint('security', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
TOK=os.path.join(STO,'csrf_token.txt')

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
    except Exception: return {}

def _token():
    if not os.path.exists(TOK):
        open(TOK,'w',encoding='utf-8').write(secrets.token_urlsafe(32))
    return open(TOK,'r',encoding='utf-8').read().strip()

@security_bp.route('/api/csrf/token')
def token():
    t=_token()
    return jsonify({'token': t})

@security_bp.route('/api/security/get')
def get_():
    c=_cfg().get('security',{})
    return jsonify({'csrf_enforce': bool(c.get('csrf_enforce')), 'cors_allow_origin': c.get('cors_allow_origin') or ''})

# API Key decorator for Phase 2 features
from functools import wraps

def require_api_key(f):
    """Decorator to require API key for endpoints (placeholder for now)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, just pass through - can add actual API key checking later
        return f(*args, **kwargs)
    return decorated_function

# API Key decorator for Phase 2 features
from functools import wraps

def require_api_key(f):
    """Decorator to require API key for endpoints (placeholder for now)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For now, just pass through - can add actual API key checking later
        return f(*args, **kwargs)
    return decorated_function
