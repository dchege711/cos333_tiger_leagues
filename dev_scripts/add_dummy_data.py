"""
add_dummy_data.py

Fill the database with simulated data.

@Incomplete: Focus on functions needed for the alpha first!

"""

import sys
sys.path.insert(0, "..")
from tiger_leagues import user, league

dummy_users = {"dgitau": {}, "ruio": {}, "ixue": {}, "oumeh": {}}
dummy_leagues = {"FIFA League F2018": {}, "Chess F2018": {}, "Table-Tennis F2018": {}}

def add_users():
    """
    Add dummy users to the database
    """
    dummy_info = [
        {
            "name": "Chege Gitau", "net_id": "dgitau", "room": "Spelman 67", 
            "email": "dgitau@princeton.edu", "phone_num": "555-555-5555", 
        },
        {
            "name": "Rui de Oliveira", "net_id": "ruio", "room": "Holder A45", 
            "email": "ruio@princeton.edu", "phone_num": "555-555-5555", 
        },
        {
            "name": "Ivy Xue", "net_id": "ixue", "room": "Pyne 32", 
            "email": "ixue@princeton.edu", "phone_num": "555-555-5555", 
        },
        {
            "name": "Obinna Umeh", "net_id": "oumeh", "room": "Bloomberg 28", 
            "email": "oumeh@princeton.edu", "phone_num": "555-555-5555", 
        }
    ]

    for user_info in dummy_info:
        c = user.__create_user_profile(user_info)
        print(c.fetchone())

def add_leagues():
    """
    Add dummy leagues
    """
    leagues_info = [
        {
            "league_name": "FIFA League F2018", 
            "description": "No descriptions right now", 
            "points_per_win": 3, "points_per_draw": 1, "points_per_loss": 0, 
            "registration_deadline": "2018-11-12", "additional_questions": {
                "q1": {"question": "Dummy Question FIFA", "options": "A, B, C"}
            }
        },
        {
            "league_name": "Chess F2018", 
            "description": "No descriptions right now", 
            "points_per_win": 4, "points_per_draw": 2, "points_per_loss": 0, 
            "registration_deadline": "2018-11-09", "additional_questions": {
                "q1": {"question": "Dummy Question Chess", "options": "A, B, C"}
            }
        },
        {
            "league_name": "Table-Tennis F2018", 
            "description": "No descriptions right now", 
            "points_per_win": 5, "points_per_draw": 2, "points_per_loss": 1, 
            "registration_deadline": "2018-11-01", "additional_questions": {}
        }
    ]

    for league_info in leagues_info:
        league.__create_league(league_info)
        # dummy_leagues[league_info["league_name"]]["league_id"] = results["message"]["league_id"]

def simulate_games(leagueid):
    """
    @todo: Simulate the games played for a given league.
    """
    return NotImplementedError()

if __name__ == "__main__":
    # add_users()
    add_leagues()
