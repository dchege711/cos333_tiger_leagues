"""
player.py

Exposes a blueprint that handles requests made to `/player/*` endpoint

"""

from flask import Blueprint

bp = Blueprint("player", __name__, url_prefix="/player")
