"""
player.py

Exposes a blueprint that handles requests made to `/user/*` endpoint

"""

from flask import Blueprint, render_template, session, request, flash
from . import decorators
from .models import user_model

bp = Blueprint("user", __name__, url_prefix="/user")

@bp.route("/profile/", methods=["GET"])
@decorators.login_required
def display_user_profile():
    """
    :return: ``flask.Response(mimetype-'text/html')``

    Render a template that contains user information such as: ``net_id, 
    preferred_name, preferred_email, phone_number, room_number, 
    associated_leagues``

    """
    return render_template("/user/user_profile.html", user=session.get("user"))

@bp.route("/profile/", methods=["POST"])
@decorators.login_required
def update_user_profile():
    """
    :return: ``flask.Response(mimetype-'text/html')``

    Update the information stored about a user. Render a template that contains 
    user information such as: ``net_id, preferred_name, preferred_email, 
    phone_number, room_number, associated_leagues``

    """
    session["user"] = user_model.update_user_profile(
        session.get("user"), session.get("net_id"), request.form
    )
    flash("User profile updated!")
    return render_template("/user/user_profile.html", user=session.get("user"))
    