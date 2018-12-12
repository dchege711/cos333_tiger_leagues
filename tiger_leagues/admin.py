"""
admin.py

Exposes a blueprint that handles requests made to `/admin/*` endpoint

"""

from collections import defaultdict
from random import shuffle
from math import ceil
from datetime import date, timedelta
from flask import (
    Blueprint, render_template, session, request, url_for, redirect, jsonify
)

from . import league, db

database = db.Database()
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
    @GET: The admin can view the requests to join the league and can choose
    to accept or reject the join requests
    """
    league_info = league.get_join_league_info(league_id)
    def __fetch_league_requests():
        league_response_table_name = "league_responses_{}".format(league_id)
        join_requests = database.execute(
            "SELECT {}.*, users.name FROM {}, users WHERE users.user_id = {}.user_id", 
            dynamic_table_or_column_names=[
                league_response_table_name,
                league_response_table_name,
                league_response_table_name
            ]
        )
        return join_requests

    if request.method == "GET":
        join_requests = __fetch_league_requests()
        return render_template(
            "/admin/approve_members.html", league_info=league_info, 
            join_requests=join_requests
        )
    
    if request.method == "POST":
        available_statuses = {
            league.STATUS_ADMIN, league.STATUS_DENIED, league.STATUS_MEMBER, 
            league.STATUS_PENDING
        }
        league_statuses = request.json # {1: "admin", 23: "member"}
        for value in league_statuses.values():
            if value not in available_statuses:
                return jsonify({
                    "success": False, "status": 200,
                    "message": "{} is not a valid status".format(value)
                })

        for user_id, user_status in league_statuses.items():
            database.execute(
                "UPDATE {} SET status=%s WHERE user_id=%s;",
                dynamic_table_or_column_names=["league_responses_{}".format(league_info["league_id"])],
                values=[user_status, user_id]
            )

        join_requests = __fetch_league_requests()
        user_id_to_status = {}
        for join_request in join_requests:
            user_id_to_status[join_request["user_id"]] = join_request["status"]

        return jsonify({
            "success": True, "status": 200, "message": user_id_to_status
        })

@bp.route("/<int:league_id>/start-league/", methods=["GET", "POST"])
def start_league(league_id):
    """
    @GET: Render a template for setting the league configurations.
    """
    league_info = league.get_join_league_info(league_id)

    if request.method == "GET":
        league_response_table_name = "league_responses_{}".format(league_id)
        cursor = database.execute(
            "SELECT status FROM {};",
            dynamic_table_or_column_names=[league_response_table_name]
        )
        registration_stats = defaultdict(lambda: 0)
        for row in cursor:
            registration_stats[row["status"]] += 1
            registration_stats["total_count"] += 1

        return render_template(
            "/admin/start_league.html", league_info=league_info,
            registration_stats=registration_stats
        )

    if request.method == "POST":
        allocations = request.json # {1: [{"name": "Chege", "user_id": 1}, ...]}
        if not allocations: return jsonify({
            "success": False, "message": "Cannot create an empty league"
        })

        # Assert that the allocations have the expected structure
        active_league_players = __fetch_active_league_players(league_id)
        active_player_ids = {player["user_id"] for player in active_league_players}
        num_players_per_div = None
        for division_players in allocations.values():
            if num_players_per_div is None:
                num_players_per_div = len(division_players)
            elif abs(len(division_players) - num_players_per_div) > 1:
                return jsonify({
                    "success": False, "message": "Invalid data detected!"
                })
            for player_object in division_players:
                try: active_player_ids.remove(player_object["user_id"])
                except KeyError: return jsonify({
                    "success": False, "message": "Invalid data detected!"
                })
        if active_player_ids: return jsonify({
            "success": False, "message": "Invalid data detected!"
        })

        # Delete any existing fixtures
        database.execute(
            "DELETE FROM match_info WHERE league_id = %s", values=[league_id]
        )
        
        # Generate the fixtures for each division
        timeslot_length = timedelta(days=league_info["match_frequency_in_days"])
        match_deadline = date.today() + timedelta(days=1) + timeslot_length
        for division_id, division_players in allocations.items():
            fixtures = __fixture_generator([x["user_id"] for x in division_players])
            deadline = match_deadline
            for current_matches in fixtures:
                for matchup in current_matches:
                    database.execute(
                        (
                            "INSERT INTO match_info (user_id_1, user_id_2, league_id, "
                            "division_id, deadline) VALUES (%s, %s, %s, %s, %s);"
                        ), 
                        values=[
                            matchup[0], matchup[1], league_id, division_id, deadline
                        ]
                    )
                deadline += timeslot_length
        
        return jsonify({
            "success": True, "message": "Fixtures successfully created!"
        })

def __fetch_active_league_players(league_id):
    """
    @returns List[DictRow]: a list of all players in the league who are eligible 
    to play league games.

    """
    table_name = "league_responses_{}".format(league_id)
    cursor = database.execute(
        "SELECT users.user_id, users.name FROM {}, users WHERE (status = %s "
        "OR status = %s) AND users.user_id = {}.user_id;",
        values=[league.STATUS_ADMIN, league.STATUS_MEMBER],
        dynamic_table_or_column_names=[table_name, table_name]
    )
    return cursor.fetchall()

@bp.route("/<int:league_id>/start-league/allocate-divisions/", methods=["POST"])
def allocate_league_divisions(league_id):
    divisions_config, received_config = {}, request.json
    allowed_params = {
        "match_frequency_in_days": float, 
        "completion_deadline": date.fromisoformat
    }
    for param in allowed_params:
        if param in received_config:
            try: 
                divisions_config[param] = allowed_params[param](received_config[param])
            except ValueError:
                return jsonify({
                    "success": False, "message": "Invalid value: {}".format(received_config[param])
                })
    
    if not divisions_config:
        return jsonify({
            "success": False, 
            "message": "Received no values. Expected: {}".format(", ".join(allowed_params.keys()))
        })

    active_league_players = __fetch_active_league_players(league_id)
    num_players = len(active_league_players)

    if "match_frequency_in_days" in divisions_config:
        database.execute(
            "UPDATE league_info SET match_frequency_in_days = %s WHERE league_id = %s",
            values=[divisions_config["match_frequency_in_days"], league_id]
        )
    else:
        divisions_config["match_frequency_in_days"] = database.execute(
            "SELECT match_frequency_in_days FROM league_info WHERE league_id = %s",
            values=[league_id]
        ).fetchone()["match_frequency_in_days"]

    num_divisions, tomorrow = 1, date.today() + timedelta(days=1)
    if "completion_deadline" in divisions_config:
        max_num_games_per_timeslot = ceil(num_players / 2.0)
        num_total_games = int(num_players * (num_players - 1) / 2.0)
        num_available_timeslots = max(1, (divisions_config["completion_deadline"] - tomorrow) / timedelta(days=divisions_config["match_frequency_in_days"]))
        num_games_per_timeslot = num_total_games / num_available_timeslots
        num_divisions = max(1, num_games_per_timeslot / max_num_games_per_timeslot)

    shuffle(active_league_players)
    num_players_per_div = ceil(num_players * 1.0 / num_divisions)
    division_allocations = {}
    i = 0
    for division_id in range(1, ceil(num_divisions) + 1):
        current_division = []
        num_players_in_current_div = min(num_players - i, num_players_per_div)
        for _2 in range(num_players_in_current_div):
            current_division.append(dict(**active_league_players[i]))
            i += 1
        division_allocations[division_id] = current_division

    league_end_date = tomorrow + timedelta(
        days=(num_players_per_div - 1) * divisions_config["match_frequency_in_days"]
    )
    return jsonify({
        "success": True, "message": {
            "divisions": division_allocations, "end_date": league_end_date.strftime("%A, %B %d, %Y")
        }
    })

@bp.route("/<int:league_id>/", methods=["GET"])
def league_homepage(league_id):
    league_info = league.get_join_league_info(league_id)
    return render_template(
        "/admin/admin_league_panel.html", league_info=league_info
    )

@bp.route("/<int:league_id>/approve/", methods=["POST"])
def approve_scores(match_id):
    return NotImplementedError()

def __fixture_generator(users):
    """
    @return `List[List[List]]` the innermost list is has 2 elements (the IDs of 
    the players involved in a game). The middle list has a collection of all the 
    games being played at a particular timeslot. The outermost list encompasses 
    all the games that will be played between all the users.

    """
    # we need a more effective of finding all the users in the league. 
    # as of right now we need to iterate through every user and the league_ids they pertain to
    length = len(users)
    odd = 0

    if length % 2 is not 0:
        odd = 1

    half = ceil(length/2)

    tempList1 = [None] * half
    tempList2 = [None] * half

    for i in range(0, half):
    	tempList1[i] = users[i]

    j = 0
    for i in range(length-1, half-1, -1):
    	tempList2[j] = users[i]
    	j += 1

    fixtures_list = []
    rounds_list = []
    pairs_list = []

    for j in range(0,length-1):
        for i in range(0, half):
            pairs_list = [tempList1[i], tempList2[i]]
            rounds_list.append(pairs_list)
            pairs_list = []
        tempList1.insert(1, tempList2[0])
        del tempList2[0]
        tempList2.append(tempList1[half])
        del tempList1[-1]
        fixtures_list.append(rounds_list)
        rounds_list = []

    return fixtures_list