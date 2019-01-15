"""
simulate_tiger_leagues.py

Add fake users to help in debugging the application.

"""

import sys
sys.path.insert(0, "..")

from random import randint, choice, sample
from datetime import date, timedelta
from math import ceil

from tiger_leagues.models import user_model, league_model, admin_model, db_model

db = db_model.Database()

def register_fake_users(num_users=40):
    """
    @returns List[dict]: the user profiles of the fake users
    """
    def generate_fake_users(n):
        """
        @yields `dict`: Represents enough information to sign up a new user.
        """
        for i in range(2, n + 2):
            yield {
                "name": "u{}".format(i), "email": "{}@not.princeton.edu".format(i),
                "phone_num": "555-555-5555", "room": "Blair A{}".format(i), 
                "net_id": "user{}".format(i)
            }
    user_profiles = []
    for fake_user in generate_fake_users(num_users):
        user_profile = user_model.update_user_profile(
            None, fake_user["net_id"], fake_user
        )
        user_profiles.append(user_profile)
    return user_profiles

def create_league(creator_user_profile, league_config=None):
    """
    :param admin_user_profile: dict

    Expected keys: ``net_id``, ``user_id``, ``league_ids``

    :kwarg league_config: dict

    If not ``None``, create leagues based on the dict. Expected keys: 
    ``league_name``, ``description``, ``points_per_win``, ``points_per_loss``, 
    ``max_num_players``, ``num_games_per_period``, ``length_period_in_days``, 
    ``registration_deadline``, ``additional_questions``.
    
    If ``league_config`` is ``None``, this method generate a random league. 

    :return: ``[dict]``
    
    The league information of the created league
    """

    if league_config is None: 
        points_per_win = randint(3, 10)
        points_per_draw = randint(1, points_per_win - 1)
        points_per_loss = randint(0, points_per_draw - 1)
        league_config = {
            "league_name": "Simulated League",
            "description": "I, for one, welcome our new simulation overlords",
            "points_per_win": points_per_win, 
            "points_per_draw": points_per_draw,
            "points_per_loss": points_per_loss,
            "max_num_players": randint(10, 100),
            "num_games_per_period": randint(1, 5),
            "length_period_in_days": randint(1, 10),
            "registration_deadline": (date.today() + timedelta(weeks=randint(1, 3))).isoformat(),
            "additional_questions": {}
        }
    results = league_model.create_league(league_config, creator_user_profile["user_id"])
    league_config["league_id"] = results["message"]
    league_config["registration_deadline"] = league_config["registration_deadline"].isoformat()
    
    return league_config

def enroll_members(league_info, player_profiles, status=league_model.STATUS_MEMBER):
    """
    :param league_info: ``dict``

    Expected keys: ``league_id``, ``additional_questions``

    :param player_profiles: ``list[dict]``

    Expected keys in each dict: ``user_id``

    :kwarg status: str

    The status to be assigned to each user

    :return: ``list[dict]``
    
    A list of updated player profiles
    """
    enrollment_data = {}
    additional_questions = league_info["additional_questions"]
    for idx, _ in enumerate(player_profiles):
        responses = {}
        for question_id in additional_questions:
            responses[question_id] = choice(
                additional_questions[question_id]["options"].split(", ")
            )
        player_profiles[idx] = league_model.process_join_league_request(
            league_info["league_id"], player_profiles[idx], responses
        )["message"]
        enrollment_data[player_profiles[idx]["user_id"]] = status

    admin_model.update_join_league_requests(
        league_info["league_id"], enrollment_data
    )

    return player_profiles

def generate_divisions_and_fixtures(league_info, desired_fixtures_config=None):
    """
    Generate the matches for the provided league.

    :param league_info: dict

    Expected keys: ``league_id``. If ``desired_fixtures_config`` is left out, 
    then ``registration_deadline``, ``num_active_players``, 
    ``num_games_per_period`` and ``length_period_in_days`` are also needed.

    :kwarg desired_fixtures_config: dict

    Expected keys: ``start_date``, ``completion_deadline``

    """
    start_date = date.fromisoformat(league_info["registration_deadline"]) - timedelta(weeks=4)
    if desired_fixtures_config is None:
        # Aim for ~4 divisions...
        days_per_match = ceil(
            league_info["length_period_in_days"] / league_info["num_games_per_period"]
        )
        completion_deadline = start_date + timedelta(
            days=(days_per_match * league_info["num_active_players"] // 4)
        )
        desired_fixtures_config = {
            "start_date": start_date.isoformat(),
            "completion_deadline": completion_deadline.isoformat()
        }

    league_divisions = admin_model.allocate_league_divisions(
        league_info["league_id"], desired_fixtures_config
    )["message"]["divisions"]

    results = admin_model.generate_league_fixtures(
        league_info["league_id"], league_divisions, start_date=start_date
    )
    if results["message"] != "Fixtures successfully created!":
        raise RuntimeError(results["message"])

def simulate_matches(league_id, admin_user_id, deadline=None, matches=None, by_admin=True):
    """
    Simulate the matches whose deadline has already passed.
    """
    if matches is None:
        matches = db.execute(
            "SELECT * FROM match_info WHERE league_id = %s AND deadline < %s;",
            values=[league_id, deadline]
        )
    for match in matches:
        score_1, score_2 = randint(0, 5), randint(0, 5)
        if by_admin:
            admin_model.approve_match({
                "score_user_1": randint(0, 5), "score_user_2": randint(0, 5),
                "match_id": match["match_id"]
            }, admin_user_id)
        else:
            score_report_1 = {
                "my_score": score_1, "opponent_score": score_2, "match_id": match["match_id"]
            }
            if randint(0, 6) <= 3: 
                score_report_2 = score_report_1 # Probably submit a non-matching score
            else: score_report_2 = {
                "my_score": score_2, "opponent_score": score_1, "match_id": match["match_id"]
            }
            # Randomly choose who submits the score last...
            if randint(0, 1) == 0:
                league_model.process_player_score_report(
                    match["user_1_id"], score_report_1
                )
                league_model.process_player_score_report(
                    match["user_2_id"], score_report_2
                )
            else:
                league_model.process_player_score_report(
                    match["user_2_id"], score_report_2
                )
                league_model.process_player_score_report(
                    match["user_1_id"], score_report_1
                )
                

def main():
    """
    Simulate different use cases for the app
    """
    try:
        net_id = sys.argv[1]
    except IndexError:
        raise RuntimeError("Usage: python simulate_users.py net_id")

    try:
        net_id_2 = sys.argv[2]
    except IndexError:
        net_id_2 = net_id + "_duplicate"

    main_user_profile = user_model.update_user_profile(
        None, net_id, {
            "name": net_id, "net_id": net_id, 
            "email": "{}@princeton.edu".format(net_id),
            "phone_num": "555-555-5555", "room": "Blair A57"  
        }
    )

    other_user_profile = user_model.update_user_profile(
        None, net_id_2, {
            "name": net_id_2, "net_id": net_id_2, 
            "email": "{}@princeton.edu".format(net_id_2),
            "phone_num": "555-555-5555", "room": "Blair A57"  
        }
    )

    fake_users = register_fake_users(num_users=50)
    today = date.today()

    #---------------------------------------------------------------------------
    # Create '1v1 Basketball' such that the user can join
    #---------------------------------------------------------------------------
    league_config = {
        "league_name": "1v1 Basketball",
        "description": "Hello @{} and @{}! Please join this league and let's ball :-)".format(net_id, net_id_2),
        "points_per_win": 3, "points_per_draw": 0, "points_per_loss": 0,
        "max_num_players": 30, "num_games_per_period": 2,
        "length_period_in_days": 7,
        "registration_deadline": (today + timedelta(weeks=randint(1, 3))).isoformat(),
        "additional_questions": {
            "question0": {
                "question": "Do you own a basketball?",
                "options": "Yes, No"
            }
        }
    }

    league_info = create_league(fake_users[0], league_config=league_config)
    enroll_members(league_info, fake_users[1:league_info["max_num_players"] // 2])
    print("Successfully created '1v1 Basketball'...")

    #---------------------------------------------------------------------------
    # Add the user as a member of 'FIFA League S2019'
    # Simulate all the games whose deadline has passed
    # This allows the user to simulate being part of an ongoing league
    #---------------------------------------------------------------------------

    league_config = {
        "league_name": "FIFA League S2019",
        "description": (
            "The league has been running for a while now. How well are you "
            "doing in this league? Who are you playing this week? Please submit "
            "your scores too!"),
        "points_per_win": 3, "points_per_draw": 1, "points_per_loss": 0,
        "max_num_players": 40, "num_games_per_period": 1,
        "length_period_in_days": 7,
        "registration_deadline": (today + timedelta(days=1)).isoformat(),
        "additional_questions": {
            "question0": {
                "question": "Which console do you have?",
                "options": "PlayStation 4, Xbox, I don't have a console"
            },
            "question1": {
                "question": "Which FIFA edition do you have?",
                "options": "FIFA 17, FIFA 18, FIFA 19, None"
            }
        }
    }

    league_info = create_league(fake_users[0], league_config=league_config)
    enroll_members(
        league_info, fake_users[1:(league_info["max_num_players"] - 3)]
    )
    enroll_members(league_info, [main_user_profile, other_user_profile])
    league_info["num_active_players"] = league_info["max_num_players"] - 2
    generate_divisions_and_fixtures(league_info)
    simulate_matches(league_info["league_id"], fake_users[0]["user_id"], deadline=today)
    print("Sucessfully simulated 'FIFA League S2019'...")

    #---------------------------------------------------------------------------
    # Make the user an admin of 'Badminton S2019'. 
    # Submit join requests from a couple of users.
    # Allows the user to approve/reject join requests and start the league
    #---------------------------------------------------------------------------

    league_config = {
        "league_name": "Badminton S2019",
        "description": (
            "We have made you an admin of 'Badminton S2019'. "
            "A couple of players have already requested to join. "
            "Approve/reject their requests and start the league."
        ),
        "points_per_win": 4, "points_per_draw": 2, "points_per_loss": 0,
        "max_num_players": 30, "num_games_per_period": 2,
        "length_period_in_days": 7,
        "registration_deadline": (today + timedelta(days=3)).isoformat(),
        "additional_questions": {
            "question0": {
                "question": "Do you own a racket?",
                "options": "Yes, No"
            },
            "question1": {
                "question": "Which type of shuttlecocks do you have?",
                "options": "Plastic, Feathered, I don't have any"
            }
        }
    }

    league_info = create_league(main_user_profile, league_config=league_config)
    enroll_members(
        league_info, fake_users[:league_info["max_num_players"] // 2],
        status=league_model.STATUS_PENDING
    )
    enroll_members(
        league_info, [other_user_profile], status=league_model.STATUS_ADMIN
    )
    print("Successfully created 'Badminton S2019'...")

    #---------------------------------------------------------------------------
    # Add the user as an admin of 'Ping Pong S2019'
    # Simulate all the games whose deadline has passed
    # This allows the user to simulate being the admin of an ongoing league
    #---------------------------------------------------------------------------

    league_config = {
        "league_name": "Ping Pong S2019",
        "description": (
            "Your league has been running for a while now. "
            "Approve pending score reports. Some of the score reports are already "
            "approved. This occurs when 2 players submit the same score."
        ),
        "points_per_win": 3, "points_per_draw": 1, "points_per_loss": 0,
        "max_num_players": 45, "num_games_per_period": 1,
        "length_period_in_days": 5,
        "registration_deadline": (today).isoformat(),
        "additional_questions": {
            "question0": {
                "question": "Do you own a racket?",
                "options": "Yes, No"
            }
        }
    }

    league_info = create_league(main_user_profile, league_config=league_config)
    enroll_members(
        league_info, [other_user_profile], status=league_model.STATUS_ADMIN
    )
    enroll_members(
        league_info, fake_users[:(league_info["max_num_players"] - 3)]
    )
    league_info["num_active_players"] = league_info["max_num_players"] - 2
    generate_divisions_and_fixtures(league_info)
    simulate_matches(
        league_info["league_id"], main_user_profile["user_id"],  
        deadline=today - timedelta(days=league_config["length_period_in_days"])
    )

    # Simulate some of the current set of matches
    current_matches = [x for x in league_model.get_matches_in_current_window(
        league_info["league_id"], num_periods_before=1, num_periods_after=0
    )]
    matches_to_simulate = sample(current_matches, 2 * len(current_matches) // 3)
    simulate_matches(
        league_info["league_id"], main_user_profile["user_id"], 
        matches=matches_to_simulate, by_admin=False
    )

    print("Sucessfully simulated 'Ping Pong S2019'...")

if __name__ == "__main__":
    from clean_database import clean_database
    clean_database()
    try:
        main()
    except:
        clean_database()
        raise
    