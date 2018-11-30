"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

import json
from datetime import date

from flask import (
    Blueprint, render_template, request, url_for, jsonify, session
)
from . import db, decorators
from collections import defaultdict

generic_500_msg = {
    "success": False, "status": 500, "message": "Internal Server Error"
}

database = db.Database()
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
        print(user["associated_leagues"])
        return league_homepage(user["associated_leagues"][0]["league_id"])
    
    return "Display page for a user that's not in any league"

@bp.route("/<int:league_id>/", methods=["GET"])
@decorators.login_required
def league_homepage(league_id):
    """
    Render a template for the provided league and the associated user. The 
    template should include information such as `standings, media_feed, 
    score_reports, upcoming_games`, etc.
    """
    associated_leagues = session.get("user")["associated_leagues"]
    cursor = database.execute(
        (
            "SELECT (points_per_win, points_per_draw, points_per_loss) "
            "FROM league_info WHERE league_id = %s"
        ),
        values=[league_id]
    )

    row = cursor.fetchone()
    points_per_win = row['points_per_win']
    points_per_draw = row['points_per_draw']
    points_per_loss = row['points_per_loss']

    cursor = database.execute(
        (
            "SELECT (match_id, user_id_1, user_id_2, score_user_1, score_user_2) "
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
        "/league/league_homepage.html", 
        standings=standings_info, associated_leagues=associated_leagues
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
        create_league_info["UserId"] = 0
        results = __create_league(create_league_info)
        if results["success"]: return jsonify(results)
        return "500. Internal Server Error"

def __create_league(league_info):
    """
    Create a league from the submitted data. Expected keys: `league_name`, 
    `description`, `points_per_win`, `points_per_draw`, `points_per_loss`, 
    `registration_deadline` and `additional_questions`.

    @returns `dict`: `success` is set to `True` only if the league was created. 
    If `success` is `False`, the `message` field will contain a decriptive error.
    Otherwise, the `message` field will be a `dict` keyed by `invite_url` and 
    `league_id`.

    """
    sanitized_additional_questions = {}
    for idx, question in enumerate(league_info["additional_questions"].values()):
        try:
            sanitized_additional_questions["question{}".format(idx)] = {
                "question": question["question"], "options": question["options"]
            }
        except KeyError:
            return {
                "success": False, "status": 200, 
                "message": "Malformed input detected!"
            }

    league_basics = (
        league_info["league_name"], league_info["description"], 
        league_info["points_per_win"], league_info["points_per_draw"], 
        league_info["points_per_loss"], league_info["registration_deadline"],
        json.dumps(sanitized_additional_questions)
    )
    cursor = database.execute(
        (
            "INSERT INTO league_info ("
            "league_name, description, points_per_win, points_per_draw, "
            "points_per_loss, registration_deadline, additional_questions) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s);"
        ), 
        values=league_basics
    )
    if cursor is None: return {
        "success": False, "status": 500, "message": "Internal Server Error"
    }

    cursor = database.execute("SELECT MAX(league_id) from league_info;")
    if cursor is None: return generic_500_msg
    league_id = cursor.fetchone()[0]

    # questions provided by the creator of league, given as the keys in league_info
    if sanitized_additional_questions:
        database.execute(
            (
                "CREATE TABLE league_responses_{} ("
                "user_id INT PRIMARY KEY UNIQUE, status VARCHAR(255), {});"
            ).format(
                league_id, ", ".join([
                    "{} VARCHAR(255)".format(x) for x in sanitized_additional_questions
                ])
            )
        )
    else:
        database.execute((
            "CREATE TABLE league_responses_{} ("
            "user_id INT PRIMARY KEY UNIQUE, status VARCHAR(255));"
        ).format(league_id))

    return {
        "success": True, "status": 200, 
        "message": {
            "invite_url": url_for("league.join_league", league_id=league_id, _external=True),
            "league_id": league_id
        }
    }


@bp.route("/browse", methods=["GET"])
@decorators.login_required
def browse_leagues():
    """
    @GET: Display leagues that the user can join.

    """
    ids_associated_leagues = set([
        x["league_id"] for x in session.get("user")["associated_leagues"]
    ])
    cursor = database.execute((
        "SELECT league_id, league_name, registration_deadline, description"
        " FROM league_info;"
    ))

    unjoined_leagues, today = [], date.today()
    for row in database.iterator(cursor):
        if row["league_id"] not in ids_associated_leagues:
            if today <= row["registration_deadline"]:
                unjoined_leagues.append(row)

    unjoined_leagues.sort(
        key=lambda league_info: league_info["registration_deadline"]
    )

    return str(unjoined_leagues)


@bp.route("/<int:league_id>/join", methods=["GET", "POST"])
@decorators.login_required
def join_league(league_id):
    """
    @GET: Render the form that needs to be filled by users that wish to join 
    this league.

    @POST: Process the information submitted by the form that is rendered by 
    the @GET request.
    """
    if request.method == "GET":
        league_info = __get_join_league_info(league_id)
        return render_template(
            "/league/join_league.html", league_info=league_info
        )
    if request.method == "POST":
        return NotImplementedError()

def __get_join_league_info(league_id):
    """
    @returns `dict` if the league is found, `None` otherwise.
    """
    cursor = database.execute(
        (
            "SELECT league_id, league_name, description, points_per_win, "
            "points_per_draw, points_per_loss, additional_questions, "
            "registration_deadline FROM league_info WHERE league_id = %s"
        ), 
        values=[league_id]
    )
    league_info = cursor.fetchone()
    
    if league_info is not None:
        if league_info["additional_questions"]:
            league_info["additional_questions"] = json.loads(league_info["additional_questions"])
        league_info["registration_deadline"] = league_info["registration_deadline"].strftime("%A, %B %d, %Y")

    return league_info
    