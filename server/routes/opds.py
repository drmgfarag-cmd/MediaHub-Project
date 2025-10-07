from flask import Blueprint, Response
opds_bp = Blueprint('opds', __name__)

@opds_bp.route('/opds/feed')
def feed():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>MediaHub OPDS</title></feed>"""
    return Response(xml, mimetype='application/atom+xml')

@opds_bp.route('/opds/books/comics')
def comics():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Comics</title></feed>"""
    return Response(xml, mimetype='application/atom+xml')


@opds_bp.route('/opds/books')
def books():
    xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Books</title></feed>"""
    return Response(xml, mimetype='application/atom+xml')
