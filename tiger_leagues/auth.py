"""
auth.py

Handles authentication-related requests e.g. `login`, `logout`
Exposes a blueprint that handles requests made to `/auth/*` endpoint

"""

from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/auth")