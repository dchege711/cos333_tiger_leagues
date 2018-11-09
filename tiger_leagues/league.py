"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

from flask import Blueprint

bp = Blueprint("league", __name__, url_prefix="/league")

