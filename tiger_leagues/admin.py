"""
admin.py

Exposes a blueprint that handles requests made to `/admin/*` endpoint

"""

from flask import (
    Blueprint, render_template, session, request, url_for, redirect, jsonify
)

from .models import admin_model, league_model

bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.before_request
def admin_status_required():
    """
    A decorator function that asserts that a user has admin privileges for the 
    requested URL.

    http://flask.pocoo.org/docs/1.0/api/#flask.Flask.before_request
    """
    if session.get("user") is None:
        return redirect(url_for("auth.index"))

    parts = request.path.split("/admin/")
    if len(parts) < 2:
        return redirect(url_for("league.index"))

    league_id = parts[1].split("/")[0]
    associated_leagues = session.get("user")["associated_leagues"]
    if league_id not in associated_leagues or associated_leagues[league_id]["status"] != "admin":
        return redirect(url_for("league.index"))
    # If nothing has been returned, the request will be passed to its handler
    return None

@bp.route("/<int:league_id>/approve-members/", methods=["GET", "POST"])
def league_requests(league_id):
    """
    @GET: An admin can view the requests to join the league and can choose
    to accept or reject the join requests

    @POST: An admins can set the join statuses of the users who requested to 
    join the league.

    """
    league_info = league_model.get_league_info(league_id)

    if request.method == "GET":
        join_requests = admin_model.get_join_league_requests(league_id)
        return render_template(
            "/admin/approve_members.html", league_info=league_info, 
            join_requests=join_requests
        )
    
    if request.method == "POST":
        return jsonify(
            admin_model.update_join_league_requests(
                league_id, request.json
            )
        )

    return NotImplementedError()

@bp.route("/<int:league_id>/start-league/", methods=["GET", "POST"])
def start_league(league_id):
    """
    @GET: Render a template for setting the league configurations.
    """
    league_info = league_model.get_league_info(league_id)

    if request.method == "GET":
        registration_stats = admin_model.get_registration_stats(league_id)
        return render_template(
            "/admin/start_league.html", league_info=league_info,
            registration_stats=registration_stats
        )

    if request.method == "POST":
        return jsonify(
            admin_model.generate_league_fixtures(
                league_id, request.json
            )
        )
    
    return NotImplementedError()

@bp.route("/<int:league_id>/start-league/allocate-divisions/", methods=["POST"])
def allocate_league_divisions(league_id):
    """
    @GET: return a JSON containing allocations of players in a league into 
    divisions
    """
    return jsonify(
        admin_model.allocate_league_divisions(
            league_id, request.json
        )
    )

@bp.route("/<int:league_id>/", methods=["GET"])
def league_homepage(league_id):
    """
    @GET: Return the league admin panel
    """
    league_info = league_model.get_league_info(league_id)
    return render_template(
        "/admin/admin_league_panel.html", league_info=league_info
    )
