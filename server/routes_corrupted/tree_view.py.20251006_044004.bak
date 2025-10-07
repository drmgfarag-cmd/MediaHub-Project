from flask import Blueprint, jsonify
import os, json
tree_bp = Blueprint('tree', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
LIB  = os.path.join(STO, 'library_index.json')

def add(node, parts, full):
    if not parts: return
    head, *tail = parts
    cur = node.setdefault(head, {"_children":{}, "_count":0})
    cur["_count"] += 1
    if tail:
        add(cur["_children"], tail, full)

@tree_bp.route('/api/tree')
def tree():
    try:
        idx=json.load(open(LIB,'r',encoding='utf-8'))
    except Exception:
        idx=[]
    root={}
    for it in idx[:5000]:
        parts=(it.get('path','/')).split('/')
        add(root, parts[1:-1], it.get('path',''))
    return jsonify(root)
