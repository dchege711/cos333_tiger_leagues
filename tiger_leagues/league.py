"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

from flask import (
    Blueprint, render_template, request, url_for, jsonify, session, redirect, flash
)
from . import decorators
from .models import league_model, user_model

bp = Blueprint("league", __name__, url_prefix="/league")

@bp.route("/", methods=["GET"])
@decorators.login_required
def index():
    """
    A user that already has an account will be redirected here. The user details 
    will be present in the session object. The user might be in none or multiple 
    leagues.

    Choose a suitable league id (if possible) and redirect to to 
    `league_homepage(leagueid)`

    """
    user = session.get("user")

    if user["associated_leagues"]:
        return league_homepage(list(user["associated_leagues"].keys())[0])
    
    return redirect(url_for(".browse_leagues"))

@bp.route("/<int:league_id>/", methods=["GET"])
@decorators.login_required
def league_homepage(league_id):
    """
    Render a template for the provided league and the associated user. The 
    template should include information such as `standings, media_feed, 
    score_reports, upcoming_matches`, etc.
    """
    associated_leagues = session.get("user")["associated_leagues"]
    standings = league_model.get_league_standings(
        league_id, associated_leagues[str(league_id)]["division_id"]
    )
    user_id = session.get("user")["user_id"]
    report_scores, _ = league_model.get_upcoming_matches(
        user_id, league_id, associated_leagues[str(league_id)]["division_id"]
    )
    return render_template(
        "/league/league_homepage.html", 
        standings=standings,
        report_scores=report_scores, 
        associated_leagues=associated_leagues, 
        league_name=associated_leagues[str(league_id)]["league_name"]
    )

@bp.route("/<int:league_id>/user/<string:net_id>", methods=["GET"])
@decorators.login_required
def league_member(league_id, net_id):
    """
    Render a template for the provided league and league member. The 
    template should include information such as ``, etc.

    @param int `user_id`: the ID of the associated user.

    @param int `league_id`: a list of all the league IDs that a user is associated with
    """
    associated_leagues = session.get("user")["associated_leagues"]
    standings = league_model.get_league_standings(
        league_id, associated_leagues[str(league_id)]["division_id"])

    return render_template(
        "/league/league_member.html", 
        user=session.get("user"), standings=standings, 
        league_name=associated_leagues[str(league_id)]["league_name"]
    )

@bp.route("/create", methods=["GET", "POST"])
@decorators.login_required
def create_league():
    """
    @GET: Render a template that can be used to create a new league.

    @POST: Create a league from the submitted data.
    """
    if request.method == "GET":
        return render_template("/league/create_league.html")
    elif request.method == "POST":
        create_league_info = request.json
        user_profile = session.get("user")
        results = league_model.create_league(create_league_info, user_profile)
        if results["success"]:
            league_id = results["message"]
            results["message"] = {
                "league_id": league_id,
                "invite_url": url_for("league.join_league", league_id=league_id, _external=True)
            }
        
        session["user"] = user_model.get_user(user_profile["net_id"])
        return jsonify(results)

@bp.route("/browse/", methods=["GET"])
@decorators.login_required
def browse_leagues():
    """
    @GET: Display leagues that the user can join.

    """
    return render_template(
        "/league/browse.html", 
        leagues=league_model.get_leagues_not_yet_joined(session.get("user"))
    )

@bp.route("/<int:league_id>/join/", methods=["GET", "POST"])
@decorators.login_required
def join_league(league_id):
    """
    @GET: Render the form that needs to be filled by users that wish to join 
    this league.

    @POST: Process the information submitted by the form that is rendered by 
    the @GET request.
    """

    results = league_model.get_league_info_if_joinable(league_id)
    if not results["success"]: 
        return render_template(
            "/league/join_league.html", error=results["message"]
        )

    league_info = results["message"]
    user_profile = session.get("user")

    if request.method == "GET":
        previous_responses = league_model.get_previous_responses(
            league_id, user_profile
        )
        return render_template(
            "/league/join_league.html", 
            league_info=league_info, previous_responses=previous_responses
        )

    if request.method == "POST":
        results = league_model.process_join_league_request(
            league_id, user_profile, request.form
        )
        if results["success"]: 
            session["user"] = results["message"]
            flash("Request Submitted!")
        else:
            flash(results["message"])
        return redirect(url_for("league.browse_leagues"))

    return NotImplementedError()

@bp.route("/<int:league_id>/leave-league/", methods=["POST"])
@decorators.login_required
def leave_league(league_id):
    """
    @POST process requests to leave a given league
    """
    user_profile = session.get("user")
    success = league_model.process_leave_league_request(league_id, user_profile)
    session["user"] = user_model.get_user(user_profile["net_id"])
    return jsonify({"success": success})
