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

def error_page(e):
    """
    General error page
    
    """
    return render_template("error.html", e = e)


