from flask import Blueprint, jsonify, request
import os, json, re
from routes.auto_select import _pool, _load as _aload, RULES
autoex_bp = Blueprint('autoex', __name__)

def _why_from_title(title):
    t=title or ''
    why=[]
    if re.search(r'(?i)\\b(2160p|UHD|4K)\\b', t): why.append('4K')
    if re.search(r'(?i)\\b(HDR10|HDR)\\b', t): why.append('HDR')
    if re.search(r'(?i)\\b(DV|Dolby\\.Vision|DoVi)\\b', t): why.append('Dolby Vision')
    if re.search(r'(?i)\\b(Atmos|TrueHD\\.Atmos|EAC3\\.Atmos)\\b', t): why.append('Dolby Atmos')
    m=re.search(r'(?i)\\b(\\d+(?:\\.\\d+)?)\\s?GB\\b', t)
    if m: why.append(m.group(0)+' size')
    return why

@autoex_bp.route('/api/auto/candidates_explain')
def explain():
    try:
        q=(request.args.get('q') or '').strip()
        if not q: return jsonify({'explain':'(empty)'})
        rules=_aload(RULES, {})
        pool=_pool(q, rules)
        if not pool: return jsonify({'explain':'No candidates'})
        b=pool[0]
        why=set(_why_from_title(b.get('title') or '') + _why_from_title(b.get('link') or ''))
        return jsonify({'best': b, 'explain': ' · '.join(why) or 'Heuristics matched (default order)'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
