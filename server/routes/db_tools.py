from flask import Blueprint, jsonify, request
import os, json
from db.sqlite_index import ensure, migrate_from_json, query

db_bp = Blueprint('db', __name__)

@db_bp.route('/api/db/migrate', methods=['POST'])
def migrate():
    migrate_from_json()
    return jsonify({'ok': True})

@db_bp.route('/api/db/query')
def q():
    q=request.args.get('q',''); typ=request.args.get('type'); n=int(request.args.get('n','200') or 200)
    return jsonify({'ok':True,'items': query(q, typ, n)})
