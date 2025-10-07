from flask import Blueprint, Response
opds_bp = Blueprint('opds', __name__)

@opds_bp.route('/opds/feed')
def feed():
    try:
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom"><title>MediaHub OPDS</title></feed>"""
        return Response(xml, mimetype='application/atom+xml')

        @opds_bp.route('/opds/books/comics')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def comics():
    try:
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom"><title>Comics</title></feed>"""
        return Response(xml, mimetype='application/atom+xml')


        @opds_bp.route('/opds/books')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def books():
    try:
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom"><title>Books</title></feed>"""
        return Response(xml, mimetype='application/atom+xml')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
