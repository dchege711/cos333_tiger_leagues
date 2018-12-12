"""
league.py

Exposes a blueprint that handles requests made to `/league/*` endpoint

"""

import json
from datetime import date
from collections import defaultdict
from functools import cmp_to_key

from . import db_model

generic_500_msg = {
    "success": False, "status": 500, "message": "Internal Server Error"
}

STATUS_PENDING = "pending"
STATUS_MEMBER = "member"
STATUS_DENIED = "denied"
STATUS_ADMIN = "admin"
STATUS_INACTIVE = "inactive"

db = db_model.Database()

def get_league_standings(league_id, division_id):
    """
    @param int `league_id`: The ID of the league

    @param int `division_id`: The ID of the division within the league

    @returns List[dict]: The sorted league standings
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

    cursor = db.execute(
        (
            "SELECT match_id, user_id_1, user_id_2, score_user_1, score_user_2 "
            "FROM match_info WHERE league_id = %s AND division_id = %s"
        ),
        values=[league_id, division_id]
    )

    standings_info = {}
    for row in cursor:
        user_id_1 = row['user_id_1']
        user_id_2 = row['user_id_2']

        if user_id_1 not in standings_info:
            standings_info[user_id_1] = defaultdict(lambda: 0)
        if user_id_2 not in standings_info:
            standings_info[user_id_2] = defaultdict(lambda: 0)

        standings_info[user_id_1]['goals_for'] += row['score_user_1']
        standings_info[user_id_2]['goals_for'] += row['score_user_2']
        standings_info[user_id_1]['goals_allowed'] += row['score_user_2']
        standings_info[user_id_2]['goals_allowed'] += row['score_user_1']
        if (row['score_user_1'] > row['score_user_2']):
            standings_info[user_id_1]['wins'] += 1
            standings_info[user_id_1]['points'] += points_per_win
            standings_info[user_id_2]['losses'] += 1
            standings_info[user_id_2]['points'] += points_per_loss
        elif (row['score_user_1'] < row['score_user_2']):
            standings_info[user_id_2]['wins'] += 1
            standings_info[user_id_2]['points'] += points_per_win
            standings_info[user_id_1]['losses'] += 1
            standings_info[user_id_1]['points'] += points_per_loss
        else:
            standings_info[user_id_1]['draws'] += 1
            standings_info[user_id_1]['points'] += points_per_draw
            standings_info[user_id_2]['draws'] += 1
            standings_info[user_id_2]['points'] += points_per_draw

    for user_id in standings_info:
        cursor = db.execute(
            (
                "SELECT name FROM users WHERE user_id = %s"
            ),
            values=[user_id]
        )
        standings_info[user_id]['name'] = cursor.fetchone()['name']
        standings_info[user_id]['user_id'] = user_id
        standings_info[user_id]['goal_diff'] = standings_info[user_id]['goals_for'] - standings_info[user_id]['goals_allowed']

    def standings_cmp(a, b):
        """
        A comparator function for sorting the standings
        """
        if a["points"] > b["points"]: return 1
        if a["points"] < b["points"]: return -1
        else:
            if a["goal_diff"] > b["goal_diff"]: return 1
            if a["goal_diff"] < b["goal_diff"]: return -1
            return a["losses"] + a["draws"] + a["wins"] - b["losses"] - b["draws"] - b["wins"]

    standings = [x for x in standings_info.values()]
    standings.sort(key=cmp_to_key(standings_cmp))

    return standings

def create_league(league_info, creator_user_profile):
    """
    Create a league from the submitted data. 
    
    @param dict `league_info`: Expected keys `league_name`, 
    `description`, `points_per_win`, `points_per_draw`, `points_per_loss`, 
    `registration_deadline` and `additional_questions`.

    @param dict `creator_user_profile`: the user who created this league

    @returns `dict`: `success` is set to `True` only if the league was created. 
    If `success` is `False`, the `message` field will contain a decriptive error.
    Otherwise, the `message` field will be an `int` representing the league ID

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
    creator_user_id = creator_user_profile["user_id"]

    league_basics = {
        "creator_user_id": creator_user_id,
        "league_name": league_info["league_name"], 
        "description": league_info["description"], 
        "points_per_win": league_info["points_per_win"], 
        "points_per_draw": league_info["points_per_draw"], 
        "max_num_players": league_info["max_num_players"], 
        "match_frequency_in_days": league_info["match_frequency_in_days"],
        "points_per_loss": league_info["points_per_loss"], 
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

    db.execute(
        "UPDATE users SET league_ids = %s WHERE user_id = %s;",
        values=[
            ", ".join(str(x) for x in creator_user_profile["league_ids"] + [league_id]),
            creator_user_id
        ]
    )

    return {"success": True, "message": league_id}

def get_league_info(league_id):
    """
    @returns `dict` Keys: `league_id`, `league_id`, `league_name`, `description`, 
    `points_per_win`, `points_per_draw`, `points_per_loss`, 
    `additional_questions`, `registration_deadline`

    @returns `None` if the league_id is not found
    """
    cursor = db.execute(
        (
            "SELECT league_id, league_name, description, points_per_win, "
            "points_per_draw, points_per_loss, additional_questions, "
            "registration_deadline, match_frequency_in_days, max_num_players "
            "FROM league_info WHERE league_id = %s"
        ), 
        values=[league_id]
    )
    league_info = cursor.fetchone()
    
    if league_info is not None:
        if league_info["additional_questions"]:
            league_info["additional_questions"] = json.loads(league_info["additional_questions"])

    return league_info

def get_leagues_not_yet_joined(user_profile):
    """
    @param dict `user_profile`: the user profile of the user

    @return List[DictRow]: Each item has `league_id`, `league_name`, 
    `registration_deadline` and `description` as keys.

    """
    ids_associated_leagues = set(user_profile["associated_leagues"].keys())
    cursor = db.execute((
        "SELECT league_id, league_name, registration_deadline, description"
        " FROM league_info;"
    ))

    unjoined_leagues, today = [], date.today()
    for row in db.iterator(cursor):
        if row["league_id"] not in ids_associated_leagues:
            if today <= row["registration_deadline"]:
                unjoined_leagues.append(row)

    unjoined_leagues.sort(
        key=lambda league_info: league_info["registration_deadline"]
    )

    return unjoined_leagues

def get_league_info_if_joinable(league_id):
    """
    @param int `league_id`: The ID of the league

    @returns `dict`: If `succcess` is `False`, `message` will contain a 
    descriptive error message. If `success` is `True`, `message` will contain 
    the league information needed to join the league.
    """

    league_info = get_league_info(league_id)

    # If the league doesn't exist, let the user know
    if league_info is None: 
        return {
            "success": False, "message": "League not found"
        }

    # If the league's deadline is already passed, communicate that to the user
    today = date.today()
    if today > league_info["registration_deadline"]:
        return {
            "success": False,
            "message": "The League's registration deadline ({}) has passed".format(
                league_info["registration_deadline"].strftime("%A, %B %d, %Y")
            )
        }

    return {"success": True, "message": league_info}

def get_previous_responses(league_id, user_profile):
    """
    @param int `league_id`: The ID of the league

    @param dict `user_profile`: A representation of the user as stored in the 
    session object.

    @returns `None`: if the user has not tried to join this league before

    @returns `DictRow`: the responses that the user previously entered while 
    trying to join this league.

    """
    ids_associated_leagues = set(user_profile["associated_leagues"].keys())
    if league_id not in ids_associated_leagues:
        return None

    return db.execute(
        "SELECT * from {} WHERE user_id = %s", 
        dynamic_table_or_column_names=["league_responses_{}".format(league_id)],
        values=[user_profile["user_id"]]
    ).fetchone()

def process_join_league_request(league_id, user_profile, submitted_data):
    """
    @param int `league_id` the ID of this league

    @param dict `user_profile`: the user data as stored in the session object

    @returns `dict`: If `succcess` is `False`, `message` will contain a 
    descriptive error message. If `success` is `True`, `message` will contain a 
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
    @param int `league_id`: The ID of the league

    @param dict `user_profile`: A representation of the user as stored in the 
    session object.

    @return `bool`: `True` if the user was successfully removed from the league

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
