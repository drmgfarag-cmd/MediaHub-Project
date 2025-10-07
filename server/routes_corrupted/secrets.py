from flask import Blueprint, jsonify, request
import os, json, base64, secrets as pysec, hashlib
from typing import Dict

secrets_bp = Blueprint('secrets', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
F=os.path.join(STO,'secrets.json')
M=os.path.join(STO,'secrets.meta')

try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.fernet import Fernet, InvalidToken
    HAVE_CRYPTO=True
except Exception:
    HAVE_CRYPTO=False

def _load():
    try: return json.load(open(F,'r',encoding='utf-8'))
        except Exception: return {}

def _meta():
        try: return json.load(open(M,'r',encoding='utf-8'))
        except Exception: return {}

def _save(obj:Dict):
    tmp=F+'.tmp'; json.dump(obj, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, F)

def _derive_key(passphrase:str, salt:bytes):
        if not HAVE_CRYPTO: return None
    kdf=PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode('utf-8')))

def _fernet():
    meta=_meta()
    if not HAVE_CRYPTO or 'salt' not in meta or 'hint' not in meta:
        return None
    key=os.environ.get('MEDIAHUB_SECRET_KEY','')
    if not key and os.path.exists(os.path.join(STO,'secrets.pass')):
        key=open(os.path.join(STO,'secrets.pass'),'r',encoding='utf-8').read().strip()
        if not key: return None
    k=_derive_key(key, base64.b64decode(meta['salt']))
    return Fernet(k) if k else None

@secrets_bp.route('/api/secrets/set_master', methods=['POST'])
def set_master():
    try:
        js=request.get_json(silent=True) or {}
        passphrase=(js.get('passphrase') or '').strip()
        if not passphrase: return jsonify({'error':'passphrase required'}), 400
        salt=os.urandom(16)
        meta={'salt': base64.b64encode(salt).decode('ascii'), 'hint': 'PBKDF2-HMAC-SHA256'}
        tmp=M+'.tmp'; json.dump(meta, open(tmp,'w',encoding='utf-8'), indent=2); os.replace(tmp, M)
        # store pass if requested
        if js.get('store','file'):
        open(os.path.join(STO,'secrets.pass'),'w',encoding='utf-8').write(passphrase)
        return jsonify({'ok':True})


        @secrets_bp.route('/api/secrets/list')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def list_():
    try:
        data=_load()
        return jsonify({'keys': sorted(list(data.keys()))})

        @secrets_bp.route('/api/secrets/put', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def put():
    try:
        js=request.get_json(silent=True) or {}
        key=(js.get('key') or '').strip()
        val=(js.get('value') or '').strip()
        if not key: return jsonify({'error':'key required'}), 400
        data=_load()
        f=_fernet()
        if f:
        tok=f.encrypt(val.encode('utf-8')).decode('ascii')
        data[key]={'enc':'fernet','v':tok}
        else:
        data[key]={'enc':'plain_b64','v': base64.b64encode(val.encode('utf-8')).decode('ascii')}
        _save(data)
        return jsonify({'ok':True})


        @secrets_bp.route('/api/secrets/get')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_():
    key=(request.args.get('key') or '').strip()
    if not key: return jsonify({'error':'key required'}), 400
    data=_load()
    if key not in data: return jsonify({'error':'not found'}), 404
    rec=data[key]
    enc=rec.get('enc'); v=rec.get('v','')
    if enc=='fernet':
        f=_fernet()
        if not f: return jsonify({'error':'locked'}), 403
        try:
            val=f.decrypt(v.encode('ascii')).decode('utf-8')
        except Exception:
            return jsonify({'error':'decrypt failed'}), 500
            return jsonify({'ok':True,'key':key,'value':val,'secure':True})
    else:
        val=base64.b64decode(v.encode('ascii')).decode('utf-8')
            return jsonify({'ok':True,'key':key,'value':val,'secure':False})


@secrets_bp.route('/api/secrets/delete', methods=['POST'])
def delete():
    try:
        js=request.get_json(silent=True) or {}
        key=(js.get('key') or '').strip()
        if not key: return jsonify({'error':'key required'}), 400
        data=_load()
        if key in data: 
        data.pop(key)
        _save(data)
        return jsonify({'ok':True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
