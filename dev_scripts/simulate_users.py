"""
simulate_users.py

Add fake users to help in debugging the application.

"""

import sys
sys.path.insert(0, "..")

from random import randint, sample
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
        for i in range(n):
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

def create_leagues(admin_user_profile, num_leagues=4):
    """
    @returns List[dict]: The league information of the created leagues
    """
    def __generate_league_info():
        for i in range(1, num_leagues + 1):
            points_per_win = randint(3, 10)
            points_per_draw = randint(1, points_per_win - 1)
            points_per_loss = randint(0, points_per_draw - 1)
            yield {
                "league_name": "League {} Pro".format(i),
                "description": "Simulation builds character",
                "points_per_win": points_per_win, 
                "points_per_draw": points_per_draw,
                "points_per_loss": points_per_loss,
                "max_num_players": randint(10, 100),
                "match_frequency_in_days": randint(0, 10) / 3.0,
                "registration_deadline": date.today() + timedelta(weeks=randint(1, 3)),
                "additional_questions": {}
            }

    league_info_list = []
    for league_info in __generate_league_info():
        results = league_model.create_league(league_info, admin_user_profile)
        admin_user_profile = user_model.get_user(admin_user_profile["net_id"])
        league_info["league_id"] = results["message"]
        league_info_list.append(league_info)

    return league_info_list

def populate_leagues(league_info_list, player_profiles):
    """
    Randomly choose players to enroll into each provided league.

    @return List[dict]: a list of updated user profiles
    """
    player_indexes = range(len(player_profiles))
    for league_info in league_info_list:
        k = min(
            len(player_profiles), randint(1, league_info["max_num_players"])
        )
        enrollment_data = {}
        for idx in sample(player_indexes, k):
            player_profiles[idx] = league_model.process_join_league_request(
                league_info["league_id"], player_profiles[idx], {}
            )["message"]
            enrollment_data[player_profiles[idx]["user_id"]] = league_model.STATUS_MEMBER

        admin_model.update_join_league_requests(
            league_info["league_id"], enrollment_data
        )

    return player_profiles

def generate_matches(league_info_list):
    """
    Generate the matches for the provided league.
    """
    today = date.today()
    for league_info in league_info_list:
        start_date = today + timedelta(days=randint(1, 5))
        completion_deadline = start_date + timedelta(
            days=randint(0, int(league_info["max_num_players"] / 2))
        )
        allocation_config = {
            "start_date": start_date.isoformat(),
            "completion_deadline": completion_deadline.isoformat()
        }
        league_divisions = admin_model.allocate_league_divisions(
            league_info["league_id"], allocation_config
        )["message"]["divisions"]

        results = admin_model.generate_league_fixtures(
            league_info["league_id"], league_divisions
        )
        if results["message"] != "Fixtures successfully created!":
            raise RuntimeError(results["message"])

    return True

def play_matches():
    """
    Generate scores and approve the matches for the provided league.
    """
    cursor = db.execute("SELECT match_id FROM match_info;")
    for row in cursor:
        admin_model.approve_match({
            "score_user_1": randint(0, 5), "score_user_2": randint(0, 5),
            "match_id": row["match_id"]
        })

if __name__ == "__main__":
    from clean_database import clean_database
    try:
        net_id = sys.argv[1]
    except IndexError:
        raise RuntimeError("Please provide a Princeton Net ID as a command line arg")

    clean_database()

    try:
        num_leagues = int(sys.argv[2])
    except IndexError:
        num_leagues = 5
    
    try:
        admin_user_profile = user_model.update_user_profile(
            None, net_id, {
                "name": net_id, "net_id": net_id, 
                "email": "{}@princeton.edu".format(net_id),
                "phone_num": "555-555-5555", "room": "Blair A57"  
            }
        )

        print("Registering 40 fake users...")
        fake_users = register_fake_users()
        
        print("Creating", num_leagues, "dummy leagues...")
        league_info_list = create_leagues(admin_user_profile, num_leagues=num_leagues)

        print("Enrolling players into leagues...")
        fake_users = populate_leagues(league_info_list, fake_users)

        print("Generating matches...")
        generate_matches(league_info_list[:ceil(num_leagues / 2.0)])

        print("Simulating all the matches...")
        play_matches()

        print("Generating more matches...")
        generate_matches([league_info_list[ceil(num_leagues / 2.0)]])
    except:
        clean_database()
        raise
    