"""
admin.py

Exposes a blueprint that handles requests made to `/admin/*` endpoint

"""

from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")
