"""
error.py

Exposes a blueprint that handles errors

"""

from flask import (
    Blueprint, render_template, request, url_for, jsonify, session, redirect, flash
)
from . import decorators
from .models import league_model, user_model

# bp = Blueprint("league", __name__, url_prefix="/league")

def page_not_found(e):
    """
    For pages that don't exist, misspelled URLs, etc.

    """
    # Refresh the user object
    return render_template('error/404.html'), 404

def forbidden(e):
    """
    For forbidden pages, like admin stuff.

    """
    # Refresh the user object
    return render_template('error/403.html'), 403

def internal_server_error(e):
    """
    For a problem on our side such as a programming bug.

    """
    # Refresh the user object
    return render_template('error/500.html'), 500