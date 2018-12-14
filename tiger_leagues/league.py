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
    score_reports, upcoming_games`, etc.
    """
    associated_leagues = session.get("user")["associated_leagues"]
    standings = league_model.get_league_standings(
        league_id, associated_leagues[str(league_id)]["division_id"]
    )
    return render_template(
        "/league/league_homepage.html", 
        standings=standings, 
        associated_leagues=associated_leagues, 
        league_name=associated_leagues[str(league_id)]["league_name"]
    )

@bp.route("/<int:league_id>/user/<string:net_id>", methods=["GET"])
@decorators.login_required
def user_lookup(league_id, net_id):
    """
    Render a template for the provided league and league member. The 
    template should include information such as ``, etc.

    @param int `user_id`: the ID of the associated user.

    @param int `league_id`: a list of all the league IDs that a user is associated with
    """

    cursor = database.execute(
        (
            "SELECT points_per_win, points_per_draw, points_per_loss, league_name "
            "FROM league_info WHERE league_id = %s"
        ),
        values=[league_id]
    )
    row = cursor.fetchone()

    points_per_win = row['points_per_win']
    points_per_draw = row['points_per_draw']
    points_per_loss = row['points_per_loss']
    league_name = row['league_name']

    cursor = database.execute(
        (
            "SELECT match_id, user_id_1, user_id_2, score_user_1, score_user_2 "
            "FROM match_info WHERE league_id = %s"
        ),
        values=[league_id]
    )

    standings_info = {}
    row = cursor.fetchone()
    while row is not None:
        key1 = row['user_id_1']
        key2 = row['user_id_2']

        if key1 not in standings_info:
            standings_info[key1] = defaultdict(lambda: 0)
        if key2 not in standings_info:
            standings_info[key2] = defaultdict(lambda: 0)

        standings_info[key1]['goals_formed'] += row['score_user_1']
        standings_info[key2]['goals_formed'] += row['score_user_2']
        standings_info[key1]['goals_allowed'] += row['score_user_2']
        standings_info[key2]['goals_allowed'] += row['score_user_1']
        if (row['score_user_1'] > row['score_user_2']):
            standings_info[key1]['wins'] += 1
            standings_info[key1]['points'] += points_per_win
            standings_info[key2]['losses'] += 1
            standings_info[key2]['points'] += points_per_loss
        elif (row['score_user_1'] < row['score_user_2']):
            standings_info[key2]['wins'] += 1
            standings_info[key2]['points'] += points_per_win
            standings_info[key1]['losses'] += 1
            standings_info[key1]['points'] += points_per_loss
        else:
            standings_info[key1]['draws'] += 1
            standings_info[key1]['points'] += points_per_draw
            standings_info[key2]['draws'] += 1
            standings_info[key2]['points'] += points_per_draw
        row = cursor.fetchone()

    for key in standings_info:
        cursor = database.execute(
            (
                "SELECT name FROM users WHERE user_id = %s"
            ),
            values=key
        )
        standings_info[key]['name'] = cursor.fetchone()['name']
        standings_info[key]['goal_diff'] = standings_info[key]['goals_formed'] - standings_info[key]['goals_allowed']

    return render_template(
        "/league/league_member.html", 
        user=session.get("user"), standings=standings_info, league_name=league_name
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
