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
    will be present in the session object.

    :return: ``flask.Response(mimetype='text/HTML')``

    If the user is a part of any leagues, render that league's homepage.

    :return: ``flask.Response(code=302)``

    If the user is not a part of any league, redirect them to a page that allows 
    them to browse available leagues.

    """
    # Refresh the user object
    session["user"] = user_model.get_user(session.get("user")["net_id"])
    user = session.get("user")

    if user["associated_leagues"]:
        return league_homepage(list(user["associated_leagues"].keys())[0])
    
    return redirect(url_for(".browse_leagues"))

@bp.route("/<int:league_id>/", methods=["GET"])
@decorators.login_required
def league_homepage(league_id):
    """
    :param league_id: ``int``

    The ID of the league associated with this request

    :return: ``flask.Response(mimetype='text/html')``

    Render a template for the provided league and the associated user. The 
    template includes information such as ``standings, media_feed, score_reports, 
    upcoming_matches``, etc.

    """
    # Refresh the user object
    session["user"] = user_model.get_user(session.get("user")["net_id"])
    user = session.get("user")

    associated_leagues = user["associated_leagues"]
    standings = league_model.get_league_standings(league_id)
    current_matches = league_model.get_players_current_matches(
        user["user_id"], league_id
    )

    return render_template(
        "/league/league_homepage.html", 
        standings=standings, league_id=league_id,
        user_division_id=associated_leagues[league_id]["division_id"],
        current_matches=current_matches, 
        associated_leagues=associated_leagues, 
        league_name=associated_leagues[league_id]["league_name"]
    )

@bp.route("/<int:league_id>/submit-score/", methods=["POST"])
@decorators.login_required
def process_score_submit(league_id):
    """
    Persist the score submitted by the user. The body of the POST object should 
    have the following keys: `my_score, opponent_score, match_id`

    :param league_id: ``int``

    The ID of the league associated with this request

    :return: ``flask.Response(mimetype='application/json')``

    The JSON object contains the keys ``success`` and ``message`` whose values 
    set appropriately.

    """
    user_id = session.get("user")["user_id"]
    return jsonify(
        league_model.process_player_score_report(user_id, request.json)
    )

@bp.route("/<int:league_id>/user/<int:user_id>/", methods=["GET"])
@decorators.login_required
def league_member(league_id, user_id):
    """
    :param league_id: ``int``

    The ID of the league associated with this request

    :param user_id: ``int``

    The ID of the user whose data should be fetched.

    :return: ``flask.Response(mimetype='text/html')``

    Render a side-by-side comparison of the currently logged in user and the 
    user whose ID was passed in the URL.

    """
    # Refresh the user object
    session["user"] = user_model.get_user(session.get("user")["net_id"])
    associated_leagues = session.get("user")["associated_leagues"]
    standings = league_model.get_league_standings(league_id)

    return render_template(
        "/league/league_member.html", 
        user=session.get("user"), standings=standings, 
        league_name=associated_leagues[league_id]["league_name"]
    )

@bp.route("/create/", methods=["GET", "POST"])
@decorators.login_required
def create_league():
    """
    :return: ``flask.Response(mimetype='text/html')``

    If responding to a GET request, render a template that can be used to 
    create a new league.

    :return: ``flask.Response(mimetype='application/json')``

    If responding to a POST request, return a JSON object confirming whether 
    the league was created. The JSON sent in the POST request should have these 
    keys: ``league_name, description, points_per_win, points_per_draw, 
    points_per_loss, registration_deadline and additional_questions``

    """
    if request.method == "GET":
        return render_template("/league/create_league.html")
    if request.method == "POST":
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
    :return: ``flask.Response(mimetype='text/html')``

    Render a page with a list of leagues that the user can request to join.

    """
    # Refresh the user object
    session["user"] = user_model.get_user(session.get("user")["net_id"])
    return render_template(
        "/league/browse.html", 
        leagues=league_model.get_leagues_not_yet_joined(session.get("user"))
    )

@bp.route("/<int:league_id>/join/", methods=["GET", "POST"])
@decorators.login_required
def join_league(league_id):
    """
    :param league_id: ``int``

    The ID of the league associated with this request

    :return: ``flask.Response(mimetype='text/html')``
    
    Render the form that needs to be filled by users that wish to join 
    this league.

    :return: ``flask.Response(mimetype='text/html')``

    Process the form submitted by the user who wants to join this league. Return 
    a JSON object that confirms the status of the join request.

    """

    results = league_model.get_league_info_if_joinable(league_id)
    if not results["success"]: 
        return render_template(
            "/league/join_league.html", error=results["message"]
        )

    league_info = results["message"]
    # Refresh the user object
    session["user"] = user_model.get_user(session.get("user")["net_id"])
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
    :param league_id: ``int``

    The ID of the league associated with this request

    :return: ``flask.Response(mimetype='application/json')``

    The JSON object contains a confirmation that the user was removed from the 
    league.
    
    """
    user_profile = session.get("user")
    success = league_model.process_leave_league_request(league_id, user_profile)
    session["user"] = user_model.get_user(user_profile["net_id"])
    return jsonify({"success": success})
