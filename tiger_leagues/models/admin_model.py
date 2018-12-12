"""
admin_model.py

Exposes functions that are used by the controller for the `/admin/*` endpoint

"""

from collections import defaultdict
from random import shuffle
from math import ceil
from datetime import date, timedelta

from . import league_model as league, db_model as database

db = database.Database()

def get_league_requests(league_id):
    """
    @param int `league_id`: The ID of the league

    @returns List[DictCursor]: A row for each user who submitted a request to 
    join this league.

    """
    league_response_table_name = "league_responses_{}".format(league_id)
    join_requests = db.execute(
        "SELECT {}.*, users.name FROM {}, users WHERE users.user_id = {}.user_id", 
        dynamic_table_or_column_names=[
            league_response_table_name,
            league_response_table_name,
            league_response_table_name
        ]
    )
    return join_requests

def update_league_requests(league_id, league_statuses):
    """
    @param int `league_id`: The ID of the league

    @param dict `league_statuses`: The keys are user_ids and the values are any 
    of the supported status strings

    @returns dict: If `success` is set, `message` will contain a user_id->status 
    matching. Otherwise, `message` will contain an error description.

    """
    league_info = league.get_join_league_info(league_id)
    available_statuses = {
        league.STATUS_ADMIN, league.STATUS_DENIED, league.STATUS_MEMBER, 
        league.STATUS_PENDING
    }
    for value in league_statuses.values():
        if value not in available_statuses:
            return {
                "success": False, "message": "{} is not a valid status".format(value)
            }

    for user_id, user_status in league_statuses.items():
        db.execute(
            "UPDATE {} SET status=%s WHERE user_id=%s;",
            dynamic_table_or_column_names=["league_responses_{}".format(league_info["league_id"])],
            values=[user_status, user_id]
        )

    join_requests = get_league_requests(league_id)
    user_id_to_status = {}
    for join_request in join_requests:
        user_id_to_status[join_request["user_id"]] = join_request["status"]

    return {
        "success": True, "status": 200, "message": user_id_to_status
    }

def get_registration_stats(league_id):
    """
    @param int `league_id`: The ID of the league

    @return dict: The keys are various join statuses and the values are their 
    frequency.

    """
    league_response_table_name = "league_responses_{}".format(league_id)
    cursor = db.execute(
        "SELECT status FROM {};",
        dynamic_table_or_column_names=[league_response_table_name]
    )
    registration_stats = defaultdict(lambda: 0)
    for row in cursor:
        registration_stats[row["status"]] += 1

    return registration_stats

def generate_league_fixtures(league_id, div_allocations):
    """
    @param int `league_id`: The ID of the league

    @param dict `div_allocations`: The keys are the division IDs. The values 
    dicts keyed by `name` and `user_id` representing a player associated with 
    the league.

    @return dict: If `success` is `False`, `message` will have a description of 
    why the call failed. Otherwise, `message` will contain a string confirming 
    that the fixtures were generated.

    """

    if not div_allocations: return {
        "success": False, "message": "Cannot create an empty league"
    }

    # Assert that the division allocations have the expected structure
    active_league_players = __fetch_active_league_players(league_id)
    active_player_ids = {player["user_id"] for player in active_league_players}
    num_players_per_div = None
    for division_players in div_allocations.values():
        if num_players_per_div is None:
            num_players_per_div = len(division_players)
        elif abs(len(division_players) - num_players_per_div) > 1:
            return {
                "success": False, 
                "message": "The number of players per division should not differ by more than 1"
            }
        for player_object in division_players:
            try: active_player_ids.remove(player_object["user_id"])
            except KeyError: return {
                "success": False, 
                "message": "{} cannot be in more than 1 division".format(
                    player_object["name"]
                )
            }
    if active_player_ids: return {
        "success": False, 
        "message": "Some players have not been allocated. Try refreshing the page to fetch an updated list of players"
    }

    # Delete any existing fixtures
    db.execute(
        "DELETE FROM match_info WHERE league_id = %s", values=[league_id]
    )
    
    # Generate the fixtures for each division
    league_info = league.get_join_league_info(league_id)
    timeslot_length = timedelta(days=league_info["match_frequency_in_days"])
    match_deadline = date.today() + timedelta(days=1) + timeslot_length

    for division_id, division_players in div_allocations.items():
        fixtures = __fixture_generator([x["user_id"] for x in division_players])
        deadline = match_deadline
        for current_matches in fixtures:
            for matchup in current_matches:
                db.execute(
                    (
                        "INSERT INTO match_info (user_id_1, user_id_2, league_id, "
                        "division_id, deadline) VALUES (%s, %s, %s, %s, %s);"
                    ), 
                    values=[
                        matchup[0], matchup[1], league_id, division_id, deadline
                    ]
                )
            deadline += timeslot_length
    
    return {
        "success": True, "message": "Fixtures successfully created!"
    }

def __fetch_active_league_players(league_id):
    """
    @returns List[DictRow]: a list of all players in the league who are eligible 
    to play league games.

    """
    table_name = "league_responses_{}".format(league_id)
    cursor = db.execute(
        "SELECT users.user_id, users.name FROM {}, users WHERE (status = %s "
        "OR status = %s) AND users.user_id = {}.user_id;",
        values=[league.STATUS_ADMIN, league.STATUS_MEMBER],
        dynamic_table_or_column_names=[table_name, table_name]
    )
    return cursor.fetchall()

def allocate_league_divisions(league_id, desired_allocation_config):
    """
    @param int `league_id`: The ID of the league

    @param dict `desired_allocation_config`: Options to use when allocating the 
    divisions. Keys may include `match_frequency_in_days`, `completion_deadline`
    """
    allocation_config = {}
    allowed_params = {
        "match_frequency_in_days": float, 
        "completion_deadline": date.fromisoformat,
        "start_date": date.fromisoformat
    }
    for param in allowed_params:
        if param in desired_allocation_config:
            try: 
                allocation_config[param] = allowed_params[param](desired_allocation_config[param])
            except ValueError:
                return {
                    "success": False, "message": "Invalid value in {}".format(desired_allocation_config[param])
                }
    
    if not allocation_config:
        return {
            "success": False, 
            "message": "Received no values. Expected: {}".format(", ".join(allowed_params.keys()))
        }

    active_league_players = __fetch_active_league_players(league_id)
    num_players = len(active_league_players)

    if "match_frequency_in_days" in allocation_config:
        db.execute(
            "UPDATE league_info SET match_frequency_in_days = %s WHERE league_id = %s",
            values=[allocation_config["match_frequency_in_days"], league_id]
        )
    else:
        allocation_config["match_frequency_in_days"] = db.execute(
            "SELECT match_frequency_in_days FROM league_info WHERE league_id = %s",
            values=[league_id]
        ).fetchone()["match_frequency_in_days"]

    start_date = allocation_config.get(
        "start_date", d=date.today() + timedelta(days=1)
    )

    if "completion_deadline" in allocation_config:
        max_num_games_per_timeslot = ceil(num_players / 2.0)
        num_total_games = int(num_players * (num_players - 1) / 2.0)
        num_available_timeslots = max(1, (allocation_config["completion_deadline"] - start_date) / timedelta(days=allocation_config["match_frequency_in_days"]))
        num_games_per_timeslot = num_total_games / num_available_timeslots
        num_divisions = max(1, num_games_per_timeslot / max_num_games_per_timeslot)
    else:
        num_divisions = 1

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

    league_end_date = start_date + timedelta(
        days=(num_players_per_div - 1) * allocation_config["match_frequency_in_days"]
    )
    return {
        "success": True, "message": {
            "divisions": division_allocations, 
            "end_date": league_end_date.strftime("%A, %B %d, %Y")
        }
    }

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
    