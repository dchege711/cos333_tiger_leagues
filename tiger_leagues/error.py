"""
error.py

Exposes a blueprint that handles errors

"""

from flask import render_template, jsonify

def report_error(tiger_leagues_exception):
    """
    General error page
    """
    if tiger_leagues_exception.jsonify:
        return jsonify(tiger_leagues_exception.todict())
    return render_template("error.html", e=tiger_leagues_exception)
    