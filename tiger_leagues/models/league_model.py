"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

import json
from datetime import date, timedelta
from math import ceil, inf
from collections import defaultdict
from functools import cmp_to_key
import traceback

from . import db_model, user_model
from .exception import TigerLeaguesException

generic_500_msg = {
    "success": False, "status": 500, "message": "Internal Server Error"
}

STATUS_PENDING = "pending"
STATUS_MEMBER = "member"
STATUS_DENIED = "denied"
STATUS_ADMIN = "admin"
STATUS_INACTIVE = "inactive"

LEAGUE_STAGE_ACCEPTING_USERS = "accepting_users"
LEAGUE_STAGE_DEADLINE_PASSED_NOT_YET_STARTED = "awaiting_admin_greenlight"
LEAGUE_STAGE_IN_PROGRESS = "league_in_progress"
LEAGUE_STAGE_COMPLETED = "league_matches_completed"
LEAGUE_STAGE_IN_PLAYOFFS = "in_playoffs"

MATCH_STATUS_APPROVED = "approved"
MATCH_STATUS_PENDING_APPROVAL = "pending_approval"

db = db_model.Database()

def update_league_standings(league_id, division_id):
    """
    Compute the new league standings and persist them into the database.

    :param league_id: int
    
    The ID of the league

    :param division_id: int
    
    The ID of the division within the league of interest

    :return: ``NoneType``

    This method affects the state of the database. It doesn't return anything. 
    To fetch the standings, call :py:meth:`.get_league_standings` instead.
    """
    cursor = db.execute(
        (
            "SELECT points_per_win, points_per_draw, points_per_loss "
            "FROM league_info WHERE league_id = %s"
        ),
        values=[league_id]
    )
    row = cursor.fetchone()

    points_per_win = row['points_per_win']
    points_per_draw = row['points_per_draw']
    points_per_loss = row['points_per_loss']

    div_standings_info = {}
    cursor = db.execute(
        "SELECT user_id FROM {} WHERE division_id = %s;", values=[division_id],
        dynamic_table_or_column_names=["league_responses_{}".format(league_id)]
    )
    for row in cursor:
        div_standings_info[row["user_id"]] = {
            "games_played": 0, "goals_for": 0, "goals_allowed": 0, "wins": 0, 
            "draws": 0, "losses": 0, "points": 0, "user_id": row["user_id"]
        }

    cursor = db.execute(
        (
            "SELECT match_id, user_1_id, user_2_id, score_user_1, score_user_2 "
            "FROM match_info WHERE league_id = %s AND division_id = %s AND status = %s;"
        ),
        values=[league_id, division_id, MATCH_STATUS_APPROVED]
    )
    
    for row in cursor:
        user_1_id = row['user_1_id']
        user_2_id = row['user_2_id']
        if user_1_id is None or user_2_id is None: continue

        div_standings_info[user_1_id]['games_played'] += 1
        div_standings_info[user_2_id]['games_played'] += 1

        div_standings_info[user_1_id]['goals_for'] += row['score_user_1']
        div_standings_info[user_2_id]['goals_for'] += row['score_user_2']

        div_standings_info[user_1_id]['goals_allowed'] += row['score_user_2']
        div_standings_info[user_2_id]['goals_allowed'] += row['score_user_1']
        
        if (row['score_user_1'] > row['score_user_2']):
            div_standings_info[user_1_id]['wins'] += 1
            div_standings_info[user_1_id]['points'] += points_per_win
            div_standings_info[user_2_id]['losses'] += 1
            div_standings_info[user_2_id]['points'] += points_per_loss
        elif (row['score_user_1'] < row['score_user_2']):
            div_standings_info[user_2_id]['wins'] += 1
            div_standings_info[user_2_id]['points'] += points_per_win
            div_standings_info[user_1_id]['losses'] += 1
            div_standings_info[user_1_id]['points'] += points_per_loss
        else:
            div_standings_info[user_1_id]['draws'] += 1
            div_standings_info[user_1_id]['points'] += points_per_draw
            div_standings_info[user_2_id]['draws'] += 1
            div_standings_info[user_2_id]['points'] += points_per_draw

    for user_id in div_standings_info:
        div_standings_info[user_id]['goal_diff'] = div_standings_info[user_id]['goals_for'] \
             - div_standings_info[user_id]['goals_allowed']
        
    def standings_cmp(a, b):
        """
        A comparator function for sorting the standings
        """
        if a["points"] > b["points"]: return 1
        if a["points"] < b["points"]: return -1
        
        if a["goal_diff"] > b["goal_diff"]: return 1
        if a["goal_diff"] < b["goal_diff"]: return -1
        return a["losses"] + a["draws"] + a["wins"] - b["losses"] - b["draws"] - b["wins"]

    standings = [x for x in div_standings_info.values()]
    standings.sort(key=cmp_to_key(standings_cmp), reverse=True)
    for rank, standing in enumerate(standings, 1): 
        standing["rank"] = rank
        standing["division_id"] = division_id
        standing["league_id"] = league_id
        div_standings_info[standing["user_id"]] = standing

    # Persist the standings in the database
    cursor = db.execute(
        "SELECT rank, user_id FROM league_standings WHERE league_id = %s AND division_id = %s;",
        values=[league_id, division_id]
    )
    for row in cursor:
        if row["rank"] is not None:
            div_standings_info[row["user_id"]]["rank_delta"] = row["rank"] - div_standings_info[row["user_id"]]["rank"]
        else:
            div_standings_info[row["user_id"]]["rank_delta"] = None

    standings_list = list(div_standings_info.values())
    if standings_list:
        db.execute(
            "DELETE FROM league_standings WHERE league_id = %s AND division_id = %s;",
            values=[league_id, division_id]
        )
        db.execute_many(
            "INSERT INTO league_standings ({}) VALUES %s;".format(
                ", ".join(standings_list[0].keys())
            ), values=standings_list
        )

    return div_standings_info

def get_league_standings(league_id):
    """
    :param league_id: int
    
    The ID of the league

    :return: ``dict[list[dict]]``
    
    The sorted league standings. The outermost dict is keyed by the division ID. 
    The ``list[dict]`` is sorted by points and then by goal difference. This 
    innermost is keyed by ``wins, losses, draws, games_played, goals_for, 
    goals_allowed, goal_diff, points, rank, rank_delta``

    If the league doesn't exist, the dict will be empty.
    """

    all_standings = defaultdict(list)
    cursor = db.execute(
        (
            "SELECT league_standings.*, users.name FROM league_standings, users "
            "WHERE league_id = %s AND league_standings.user_id = users.user_id "
            "ORDER BY division_id ASC, rank ASC;"
        ),
        values=[league_id] 
    )

    for row in cursor:
        all_standings[row["division_id"]].append(row)

    return all_standings

def get_matches_in_current_window(league_id, num_periods_before=3, 
                                  num_periods_after=3, user_id=None):
    """
    :param league_id: int
    
    The ID of the league

    :kwarg num_periods_before: int (or infinity)

    The fetched matches will have deadlines that are at least on/later than 
    ``today - num_days_between_games * num_periods_before``
    If the value is ``inf``, then all matches that have deadlines earlier than 
    today will be included in the results.
    
    :kwarg num_periods_after: int (or infinity)
    
    The fetched matches will have deadlines that are at least on/earlier than 
    ``today + num_days_between_games * num_periods_before``
    If the value is ``inf``, then all matches that have deadlines later than 
    today will be included in the results.

    :kwarg user_id: int 
    
    If set, only return matches that are associated with this user ID

    :return: ``List[DictRow]``
    
    A list of all the matches within the current time window. These are the 
    matches that are about to be played or have been played. Keys include: 
    ```match_id``` ```user_1_id```, ```user_2_id```, ```league_id```, ```division_id```, 
    ```score_user_1```, ```score_user_2```, ```status```, ```deadline```
    """
    cursor = db.execute(
        "SELECT num_games_per_period, length_period_in_days FROM league_info WHERE league_id = %s;", 
        values=[league_id]
    )

    row = cursor.fetchone()
    if row is None:
        raise TigerLeaguesException('League does not exist; it may have been deleted. \
        If you entered the URL manually, double-check the league ID.', jsonify=False)
    
    time_window_days = ceil(row["length_period_in_days"] / row["num_games_per_period"])

    date_limits = db.execute(
        "SELECT min(deadline), max(deadline) FROM match_info WHERE league_id = %s;",
        values=[league_id]
    ).fetchone()

    
    today = date.today()
    if num_periods_before == inf:
        try:
            earliest_date = min(today, date_limits["min"])
        except TypeError:
            earliest_date = today
    else:
        earliest_date = date.today() - timedelta(days=time_window_days * num_periods_before)

    if num_periods_after == inf:
        try: 
            latest_date = max(today, date_limits["max"])
        except TypeError:
            latest_date = today
    else:
        latest_date = date.today() + timedelta(days=time_window_days * num_periods_after)
    
    if user_id is not None:
        return db.execute(
            (
                "SELECT * FROM match_info WHERE league_id = %s "
                "AND (user_1_id = %s OR user_2_id = %s) "
                "AND (user_1_id IS NOT NULL AND user_2_id IS NOT NULL) "
                "AND deadline >= %s AND deadline <= %s ORDER BY deadline;"
            ),
            values=[league_id, user_id, user_id, earliest_date, latest_date]
        )
        
    return db.execute(
        (
            "SELECT * FROM match_info WHERE league_id = %s "
            "AND (user_1_id IS NOT NULL AND user_2_id IS NOT NULL) "
            "AND deadline >= %s AND deadline <= %s ORDER BY deadline;"
        ),
        values=[league_id, earliest_date, latest_date]
    )

def get_players_current_matches(user_id, league_id, num_periods_before=4, 
                                num_periods_after=4):
    """
    Unlike :py:meth:`.get_matches_in_current_window`, this method resolves the 
    opponent names as well as adding convenient fields such as ``my_score, 
    opponent_score, opponent_id, opponent_name``.

    :param user_id: int

    The ID of the player (equivalent to user)

    :param league_id: int

    The ID of the league

    :kwarg num_periods_before: int (or infinity)

    The fetched matches will have deadlines that are at least on/later than 
    ``today - num_days_between_games * num_periods_before``
    If the value is ``inf``, then all matches that have deadlines earlier than 
    today will be included in the results.
    
    :kwarg num_periods_after: int (or infinity)
    
    The fetched matches will have deadlines that are at least on/earlier than 
    ``today + num_days_between_games * num_periods_before``
    If the value is ``inf``, then all matches that have deadlines later than 
    today will be included in the results.

    :return: ``List[dict]``
    
    The player's current matches ordered by the deadline. Each dict is keyed by 
    ``match_id, league_id, division_id, status, deadline, my_score,  
    opponent_id, opponent_score, opponent_name``
    """

    relevant_matches = get_matches_in_current_window(
        league_id, user_id=user_id, num_periods_after=num_periods_after, 
        num_periods_before=num_periods_before
    )
    current_matches = []

    for match in relevant_matches:
        mutable_match = dict(**match)
        if match["user_1_id"] != user_id: 
            mutable_match["opponent_id"] = match["user_1_id"]
            mutable_match["opponent_score"] = match['score_user_1']
            mutable_match["my_score"] = match['score_user_2']
        else: 
            mutable_match["opponent_id"] = match["user_2_id"]
            mutable_match["opponent_score"] = match['score_user_2']
            mutable_match["my_score"] = match['score_user_1']

        current_matches.append(mutable_match)

    for match in current_matches:
        cursor = db.execute(
            "SELECT name FROM users WHERE user_id = %s",
            values=[match["opponent_id"]]
        )
        match["opponent_name"] = cursor.fetchone()["name"]

    return current_matches

def process_player_score_report(user_id, score_details):
    """
    :param user_id: int
    
    The ID of the user submitting the score report

    :param score_details: dict
    
    Expected keys: ``my_score``, ``opponent_score``, ``match_id``.

    :return: ```dict```
    
    Keys: ```success```, ```message```. If ```success``` is ```True```, ```message``` 
    contains the status of the match after the score has been processed. 
    Otherwise, ```message``` contains an explanation of what went wrong.

    """
    if score_details["my_score"] is None:
        return {"success": False, "message": "Score cannot be empty!"}

    elif score_details["opponent_score"] is None:
        return {"success": False, "message": "Score cannot be empty!"}


    previous_match_details = db.execute(
        "SELECT * FROM match_info WHERE match_id = %s", 
        values=[score_details["match_id"]]
    ).fetchone()
    mapping = {}
    if previous_match_details["user_1_id"] == user_id:
        mapping["my_score"] = "score_user_1"
        mapping["score_user_1"] = "my_score"
        mapping["opponent_score"] = "score_user_2"
        mapping["score_user_2"] = "opponent_score"
    else:
        mapping["my_score"] = "score_user_2"
        mapping["score_user_2"] = "my_score"
        mapping["opponent_score"] = "score_user_1"
        mapping["score_user_1"] = "opponent_score"
    
    if previous_match_details["recent_updater_id"] != user_id and \
        previous_match_details[mapping["my_score"]] == score_details["my_score"] and \
        previous_match_details[mapping["opponent_score"]] == score_details["opponent_score"]:
        match_status = MATCH_STATUS_APPROVED
    else:
        match_status = MATCH_STATUS_PENDING_APPROVAL

    db.execute(
        (
            "UPDATE match_info "
            "SET score_user_1 = %s, score_user_2 = %s, status = %s, recent_updater_id = %s "
            "WHERE match_id = %s"
        ),
        values=[
            score_details[mapping["score_user_1"]], score_details[mapping["score_user_2"]],
            match_status, user_id, score_details["match_id"]
        ]
    )

    # If the score has been approved update the standings
    if match_status == MATCH_STATUS_APPROVED:
        update_league_standings(
            previous_match_details["league_id"],
            previous_match_details["division_id"]
        )

    return {"success": True, "message": {"match_status": match_status}}

def create_league(league_info, creator_user_id):
    """
    :param league_info: dict
    
    Expected keys: ``league_name``, ``description``, ``points_per_win``, 
    ``points_per_draw``, ``points_per_loss``, ``registration_deadline``, 
    ``additional_questions``.

    :param creator_user_profile: int
    
    The ID of the user creating this league

    :return: ``dict``
    
    ``success`` is set to ``True`` only if the league was created. 
    If ``success`` is ``False``, the ``message`` field will contain a 
    decriptive error message. Otherwise, the ``message`` field will be an 
    ``int`` representing the league ID

    """
    # Assert that all required fields have been submitted
    for key in [
            "league_name", "description", "points_per_win", "points_per_draw", 
            "points_per_loss", "max_num_players", "num_games_per_period", 
            "length_period_in_days", "registration_deadline", "additional_questions"
        ]:
        if key not in league_info:
            raise TigerLeaguesException(
                "The following value is missing: {}".format(key), jsonify=True
            )

    sanitized_additional_questions = {}
    for idx, question in enumerate(league_info["additional_questions"].values()):
        try:
            sanitized_additional_questions["question{}".format(idx)] = {
                "question": question["question"], "options": question["options"]
            }
        except KeyError:
            raise TigerLeaguesException(
                "Malformed input detected in the additional questions", jsonify=True
            )

    def __validate_values(value, cast_function, error_msg, lower_limit=None, upper_limit=None):
        try:
            value = cast_function(value)
            if lower_limit is not None: assert value >= lower_limit
            if upper_limit is not None: assert value <= upper_limit
        except:
            traceback.print_exc()
            raise TigerLeaguesException(error_msg, jsonify=True)
    
    __validate_values(
        league_info["max_num_players"], int, 
        "The max number of players should be an integer that is at least 2", 2
    )
    __validate_values(
        league_info["num_games_per_period"], int, 
        "The number of games per time period should be an integer that is at least 1", 1
    )
    __validate_values(
        league_info["length_period_in_days"], int, 
        "The length of a time period should be an integer that is at least 1", 1
    )

    __validate_values(
        league_info["points_per_win"], int, 
        "The number of points awarded for a win should be an integer value",
    )

    __validate_values(
        league_info["points_per_draw"], int, 
        "The number of points awarded for a draw should be an integer value",
    )

    __validate_values(
        league_info["points_per_win"], int, 
        "The number of points deducted after a loss should be an integer value"
    )

    __validate_values(
        league_info["registration_deadline"], date.fromisoformat, 
        "The registration deadline cannot be a day in the past",
        date.today()
    )

    league_basics = {
        "creator_user_id": creator_user_id,
        "league_status": LEAGUE_STAGE_ACCEPTING_USERS,
        "league_name": league_info["league_name"], 
        "description": league_info["description"], 
        "points_per_win": league_info["points_per_win"], 
        "points_per_draw": league_info["points_per_draw"],
        "points_per_loss": league_info["points_per_loss"],
        "max_num_players": league_info["max_num_players"],
        "num_games_per_period": league_info["num_games_per_period"],
        "length_period_in_days": league_info["length_period_in_days"],
        "registration_deadline": league_info["registration_deadline"],
        "additional_questions": json.dumps(sanitized_additional_questions)
    }
    keys_in_order = list(league_basics.keys())
    cursor = db.execute(
        "INSERT INTO league_info ({}) VALUES ({}) RETURNING league_id;".format(
            ", ".join(["{}" for _ in keys_in_order]),
            ", ".join(["%({})s".format(key) for key in keys_in_order])
        ),
        dynamic_table_or_column_names=keys_in_order,
        values=league_basics
    )
    league_id = cursor.fetchone()["league_id"]

    # questions provided by the creator of league, given as the keys in league_info
    if sanitized_additional_questions:
        db.execute(
            (
                "CREATE TABLE league_responses_{} ("
                "user_id INT PRIMARY KEY UNIQUE, status VARCHAR(255), division_id INT, {});"
            ).format(
                league_id, ", ".join([
                    "{} VARCHAR(255)".format(x) for x in sanitized_additional_questions
                ])
            )
        )
    else:
        db.execute((
            "CREATE TABLE league_responses_{} ("
            "user_id INT PRIMARY KEY UNIQUE, status VARCHAR(255), division_id INT);"
        ).format(league_id))

    # Set a default row for the league creator as an admin
    db.execute(
        "INSERT INTO {} (user_id, status) VALUES (%s, %s);",
        values=[creator_user_id, STATUS_ADMIN],
        dynamic_table_or_column_names=[
            "league_responses_{}".format(league_id)
        ]
    )

    prev_league_ids = user_model.get_user(
        None, user_id=creator_user_id
    )["league_ids"]

    db.execute(
        "UPDATE users SET league_ids = %s WHERE user_id = %s;",
        values=[
            ", ".join(str(x) for x in prev_league_ids + [league_id]),
            creator_user_id
        ]
    )

    return {"success": True, "message": league_id}

def get_league_info(league_id):
    """
    :param league_id: int

    The ID of this league

    :return: ``dict``
    
    Keys: ``league_id``, ``league_id``, ``league_name``, ``description``, 
    ``points_per_win``, ``points_per_draw``, ``points_per_loss``, ``league_status``, 
    ``additional_questions``, ``registration_deadline``, ``num_games_per_period``, 
    ``length_period_in_days``, ``max_num_players``

    :raise: ``TigerLeaguesException``
    
    If the league_id is not found in the database.

    """
    cursor = db.execute(
        (
            "SELECT league_info.*, users.name, users.net_id "
            "FROM league_info, users WHERE league_id = %s AND league_info.creator_user_id = users.user_id;"
        ), 
        values=[league_id]
    )
    league_info = cursor.fetchone()
    
    if league_info is None:
        raise TigerLeaguesException(
            'League does not exist; it may have been deleted.', jsonify=False
        )

    if league_info["additional_questions"]:
        league_info["additional_questions"] = json.loads(league_info["additional_questions"])

    return league_info

def get_leagues_not_yet_joined(user_profile):
    """
    :param user_profile: dict 
    
    Expected keys: ``associated_leagues``

    :return: ``List[DictRow]``
    
    Each item is keyed by ``league_id``, ``league_name``, ``registration_deadline`` 
    and ``description``

    """
    ids_associated_leagues = set(user_profile["associated_leagues"].keys())
    cursor = db.execute((
        "SELECT league_id, league_name, registration_deadline, description, league_info.league_status, users.name, "
        "users.net_id FROM league_info, users WHERE league_info.creator_user_id = users.user_id;"
    ))

    unjoined_leagues, today = [], date.today()
    for row in cursor:
        if row["league_id"] not in ids_associated_leagues:
            if today <= row["registration_deadline"] and row["league_status"] == LEAGUE_STAGE_ACCEPTING_USERS:
                unjoined_leagues.append(row)

    unjoined_leagues.sort(
        key=lambda league_info: league_info["registration_deadline"]
    )

    return unjoined_leagues

def get_league_info_if_joinable(league_id):
    """
    :param league_id: int 
    
    The ID of the league

    :return: ``dict``
    
    If ``succcess`` is ``False``, ``message`` will contain a descriptive error 
    message. If ``success`` is ``True``, ``message`` will contain the league 
    information needed to join the league.
    """

    league_info = get_league_info(league_id)

    # If the league doesn't exist, let the user know
    if league_info is None: 
        raise TigerLeaguesException(
            "The league does not exist", jsonify=False
        )

    # If the league's deadline is already passed, communicate that to the user
    today = date.today()
    if today > league_info["registration_deadline"]:
        raise TigerLeaguesException(
            "The registration deadline for '{}' has passed ({})".format(
                league_info["league_name"],
                league_info["registration_deadline"].strftime("%A, %B %d, %Y")
            ), jsonify=False
        )

    if league_info["league_status"] != LEAGUE_STAGE_ACCEPTING_USERS:
        raise TigerLeaguesException(
            "'{}' is no longer accepting new players".format(league_info["league_name"]), 
            jsonify=False
        )

    return {"success": True, "message": league_info}

def get_previous_responses(league_id, user_profile):
    """
    :param league_id: int 
    
    The ID of the league

    :param user_profile: dict
    
    Expected keys: ``associated_leagues, user_id``

    :return: ``NoneType``
    
    If the user has not tried to join this league before

    :return: ``DictRow``
    
    The responses that the user previously entered while trying to join this 
    league.

    """
    ids_associated_leagues = set(user_profile["associated_leagues"].keys())
    if league_id not in ids_associated_leagues:
        return None

    return db.execute(
        "SELECT * from {} WHERE user_id = %s", 
        dynamic_table_or_column_names=["league_responses_{}".format(league_id)],
        values=[user_profile["user_id"]]
    ).fetchone()

def get_players_league_stats(league_id, user_id, matches=None, k=5):
    """
    :param league_id: int

    The ID of the associated league

    :param user_id: int

    The ID of the user

    :kwarg matches: ``list[dict]``

    A list of matches to calculate the player's form from. The matches should be 
    ordered such that the most recent matches appear last in the list.
    If ``NoneType``, this method queries the database for such matches.

    :kwarg k: int

    The max number of matches to calculate a player's form from.

    :return: ``dict``

    Keyed by ``success`` and ``message``. 
    If ``success`` is ``True``, ``message`` will be a dict keyed by ``rank, 
    points, player_form``
    If ``success`` is ``False``, ``message`` will contain a descriptive error 
    message.

    """
    player_standing = db.execute(
        "SELECT * FROM league_standings WHERE user_id = %s AND league_id = %s;",
        values=[user_id, league_id]
    ).fetchone()

    if player_standing is None:
        player_details = db.execute(
            (
                "SELECT name, league_name FROM users, league_info "
                "WHERE user_id = %s AND league_id = %s;"
            ),
            values=[user_id, league_id]
        ).fetchone()
        if player_details is None:
            raise TigerLeaguesException("The player was not found.", status_code=400)
        associated_leagues = user_model.get_user(None, user_id=user_id)["associated_leagues"]
        if league_id not in associated_leagues:
            raise TigerLeaguesException(
                "{} is not a member of {}".format(
                    player_details["name"], player_details["league_name"]
                ), jsonify=False
            )
        else:
            raise TigerLeaguesException(
                "{} has not started yet.".format(
                    player_details["league_name"]
                ), jsonify=False
            )

    lowest_rank = db.execute(
        "SELECT MAX(rank) FROM league_standings WHERE league_id = %s AND division_id = %s;",
        values=[league_id, player_standing["division_id"]]
    ).fetchone()["max"]

    player_stats = dict(**player_standing)
    player_stats["lowest_rank"] = lowest_rank
    if matches is None:
        matches = get_players_current_matches(
            user_id, league_id, num_periods_before=5, num_periods_after=0
        )

    player_form = []
    for match in reversed(matches):
        if match["status"] == MATCH_STATUS_APPROVED:
            form_marker = "W"
            if match["my_score"] < match["opponent_score"]: form_marker = "L"
            elif match["my_score"] == match["opponent_score"]: form_marker = "D"
            player_form.append([form_marker, match["my_score"], match["opponent_score"]])
            if len(player_form) == k: break

    player_stats["player_form"] = player_form
    return {"success": True, "message": player_stats}

def get_player_comparison(league_id, user_1_id, user_2_id):
    """
    :param league_id: int

    The ID of the associated league

    :param user_1_id: int

    The ID of the first user. By convention, user 1 is the initiator of the 
    request.

    :param user_2_id: int

    The ID of the second user

    :return: ``dict``

    Keyed by ``success`` and ``message``. 
    If ``success`` is ``True``, ``message`` will be a dict keyed by ``rank, 
    points, mutual_opponents, head_to_head, player_form``

    """
    user_1_info = user_model.get_user(None, int(user_1_id))
    user_2_info = user_model.get_user(None, int(user_2_id))

    if user_1_info is None or user_2_info is None:
        raise TigerLeaguesException('User does not exist. \
        If you entered the URL manually, double-check their user ID.', jsonify=False)

    if league_id not in user_1_info["associated_leagues"]:
        raise TigerLeaguesException('You are not a member of this league. \
        If you entered the URL manually, double-check the league ID.', jsonify=False)
    if league_id not in user_2_info["associated_leagues"]:
        raise TigerLeaguesException('User is not a member of this league. \
        If you entered the URL manually, double-check the league ID.', jsonify=False)


    user_1_matches = get_players_current_matches(
        user_1_id, league_id, num_periods_before=inf, num_periods_after=inf
    )
    user_2_matches = get_players_current_matches(
        user_2_id, league_id, num_periods_before=inf, num_periods_after=inf
    )

    user_1_stats = get_players_league_stats(league_id, user_1_id, matches=user_1_matches)["message"]
    user_2_stats = get_players_league_stats(league_id, user_2_id, matches=user_2_matches)["message"]

    # Case: The users are in different divisions so comparing them doesn't make sense
    if user_1_matches and user_2_matches and \
        user_1_matches[0]["division_id"] != user_2_matches[0]["division_id"]:
        return {
            "success": True, 
            "message": {
                "different_divisions": True,
                "user_1": user_1_stats,
                "user_2": user_2_stats,
            }
        }

    user_1_opponents = set(x["opponent_id"] for x in user_1_matches)
    user_2_opponents = set(x["opponent_id"] for x in user_2_matches)

    mutual_opponent_ids = user_1_opponents.intersection(user_2_opponents)

    head_to_head_matches = []
    if user_2_id in user_1_opponents:
        for match in user_1_matches:
            if match["opponent_id"] == user_2_id and match["status"] == MATCH_STATUS_APPROVED:
                head_to_head_matches.append(match)

    mutual_opponent_ids.discard(user_1_id)
    mutual_opponent_ids.discard(user_2_id)

    def collect_mutual_opponents(stats_obj, matches_obj):
        stats_obj["mutual_opponents"] = defaultdict(list)
        for match in matches_obj:
            if match["opponent_id"] in mutual_opponent_ids and match["status"] == MATCH_STATUS_APPROVED:
                stats_obj["mutual_opponents"][match["opponent_id"]].append(match)

    collect_mutual_opponents(user_1_stats, user_1_matches)
    collect_mutual_opponents(user_2_stats, user_2_matches)

    return {
        "success": True,
        "message": {
            "different_divisions": False,
            "user_1": user_1_stats,
            "user_2": user_2_stats,
            "head_to_head": head_to_head_matches
        }
    }

def process_join_league_request(league_id, user_profile, submitted_data):
    """
    :param league_id: int
    
    The ID of this league

    :param user_profile: dict
    
    Expected keys: ``user_id, league_ids``

    :return: ``dict``
    
    If ``succcess`` is ``False``, ``message`` will contain a descriptive error 
    message. If ``success`` is ``True``, ``message`` will contain a 
    dict containing the updated user profile.
    """
    results = get_league_info_if_joinable(league_id)
    if not results["success"]: return results

    league_info = results["message"]
    expected_info = {}
    for key in league_info["additional_questions"]:
        expected_info[key] = ""

    for key in expected_info:
        if key not in submitted_data: 
            return {
                "success": False,
                "message": "Missing {} in the submitted form".format(key)
            }
        expected_info[key] = submitted_data[key]

    expected_info["user_id"] = user_profile["user_id"]
    expected_info["status"] = STATUS_PENDING
    table_name = "league_responses_{}".format(league_id)
    db.execute(
        "DELETE FROM {} WHERE user_id = %s", values=[user_profile["user_id"]], 
        dynamic_table_or_column_names=[table_name]

    )
    db.execute(
        (
            "INSERT INTO {} ({}) VALUES ({});".format(
                "{}", ", ".join(key for key in expected_info), 
                ", ".join("%({})s".format(key) for key in expected_info)
            )
        ),
        values=expected_info,
        dynamic_table_or_column_names=[table_name]
    )

    # Indicate on the user object that they're involved in this league
    if league_id not in user_profile["league_ids"]:
        user_profile["league_ids"].append(league_id)
        db.execute(
            "UPDATE users SET league_ids = %s WHERE user_id = %s",
            values=[
                ", ".join(str(x) for x in user_profile["league_ids"]), 
                user_profile["user_id"]
            ]
        )
    
    return {"success": True, "message": user_profile}

def process_leave_league_request(league_id, user_profile):
    """
    :param league_id: int
    
    The ID of the league

    :param user_profile: dict 
    
    Expected keys: ``user_id, league_ids``

    :return: ``bool``: 
    
    ``True`` if the user was successfully removed from the league, ``False`` 
    otherwise

    """
    db.execute(
        "UPDATE {} SET status = %s WHERE user_id =  %s",
        values=[STATUS_INACTIVE, user_profile["user_id"]], 
        dynamic_table_or_column_names=["league_responses_{}".format(league_id)]
    )
    associated_league_ids = set(user_profile["league_ids"])
    if league_id in associated_league_ids:
        associated_league_ids.remove(league_id)
    db.execute(
        "UPDATE users SET league_ids=%s WHERE user_id=%s",
        values=[
            ", ".join([str(x) for x in associated_league_ids]),
            user_profile["user_id"]
        ]
    )
    return True

def process_update_league_responses(league_id, user_profile, submitted_data):
    """
    :param league_id: int
    
    The ID of this league

    :param user_profile: dict
    
    Expected keys: ``user_id, league_ids``

    :return: ``dict``
    
    If ``succcess`` is ``False``, ``message`` will contain a descriptive error 
    message. If ``success`` is ``True``, ``message`` will contain a 
    dict containing the updated user profile.
    """
    results = get_league_info_if_joinable(league_id)
    if not results["success"]: return results

    league_info = results["message"]
    expected_info = {}
    for key in league_info["additional_questions"]:
        expected_info[key] = ""

    for key in expected_info:
        if key not in submitted_data: 
            return {
                "success": False,
                "message": "Missing {} in the submitted form".format(key)
            }
        expected_info[key] = submitted_data[key]

    table_name = "league_responses_{}".format(league_id)

    row = db.execute(
        "SELECT * from {} WHERE user_id = %s", values=[user_profile["user_id"]], 
        dynamic_table_or_column_names=[table_name]
    ).fetchone()
    if row is not None:
        db.execute(
            "DELETE FROM {} WHERE user_id = %s", values=[user_profile["user_id"]], 
            dynamic_table_or_column_names=[table_name]

        )

    expected_info["user_id"] = user_profile["user_id"]
    expected_info["status"] = row["status"]

    db.execute(
        (
            "INSERT INTO {} ({}) VALUES ({});".format(
                "{}", ", ".join(key for key in expected_info), 
                ", ".join("%({})s".format(key) for key in expected_info)
            )
        ),
        values=expected_info,
        dynamic_table_or_column_names=[table_name]
    )

    # Indicate on the user object that the responses were saved
    if league_id not in user_profile["league_ids"]:
        # user_profile["league_ids"].append(league_id)
        db.execute(
            "UPDATE users SET league_ids = %s WHERE user_id = %s",
            values=[
                ", ".join(str(x) for x in user_profile["league_ids"]), 
                user_profile["user_id"]
            ]
        )
    
    return {"success": True, "message": user_profile}