"""
test_user_model.py
"""

import sys
import pytest
sys.path.insert(0, "../..")

from tiger_leagues.models import league_model, db_model, admin_model, exception
from dev_scripts import simulate_users
from math import inf
from random import randint

db = db_model.Database()

def create_league():

    fake_users = simulate_users.register_fake_users(num_users=4)
    num_fake_users = db.execute("SELECT COUNT (DISTINCT user_id) FROM users;").fetchone()["count"]
    assert num_fake_users == 4

    admin_user = fake_users[0]
    fake_users = fake_users[1:]

    fake_leagues = simulate_users.create_leagues(admin_user, num_leagues=1)
    
    simulate_users.populate_leagues(fake_leagues, fake_users)
    assert simulate_users.generate_matches(fake_leagues)

    test_league = fake_leagues[0]

    return test_league, fake_users

def test_league_methods(cleanup):

    """
    Generate scores and approve the matches for the provided league.
    """

    test_league, fake_users = create_league()

    cursor = db.execute("SELECT match_id FROM match_info;")
    for row in cursor:
        admin_model.approve_match({
            "score_user_1": randint(0, 5), "score_user_2": randint(0, 5),
            "match_id": row["match_id"]
        })

    # Change scores to take a player to the top of their divison
    # Change scores to take a player to the bottom of their division

    league_top = fake_users[1]
    league_bottom = fake_users[2]

    leader_matches = league_model.get_players_current_matches(league_top["user_id"], test_league["league_id"],
                        num_periods_before=inf, num_periods_after=inf)

    for match in leader_matches:
        if match["user_1_id"] == league_top["user_id"]:
            admin_model.approve_match({
            "score_user_1": 7, "score_user_2": 0,
            "match_id": match["match_id"]
        })
        elif match["user_2_id"] == league_top["user_id"]:
            admin_model.approve_match({
            "score_user_1": 0, "score_user_2": 7,
            "match_id": match["match_id"]
        })

    last_place_matches = league_model.get_players_current_matches(league_bottom["user_id"], test_league["league_id"],
                        num_periods_before=inf, num_periods_after=inf)

    for match in last_place_matches:
        if match["user_1_id"] == league_bottom["user_id"]:
            admin_model.approve_match({
            "score_user_1": 0, "score_user_2": 9,
            "match_id": match["match_id"]
        })
        elif match["user_2_id"] == league_bottom["user_id"]:
            admin_model.approve_match({
            "score_user_1": 9, "score_user_2": 0,
            "match_id": match["match_id"]
        })

    # Check that the altered results have affected the league standings in the desired manner
    
    leader_info = league_model.get_players_league_stats(test_league["league_id"],
                     league_top["user_id"], matches=None, k=5)

    leader_stats = leader_info["message"]
    assert leader_stats["rank"] == 1

    last_place_info = league_model.get_players_league_stats(test_league["league_id"],
                     league_bottom["user_id"], matches=None, k=5)

    last_place_stats = last_place_info["message"]
    assert last_place_stats["rank"] == last_place_stats["lowest_rank"]

    # Check that submitting scores works
    score_set = {}
    score_set["my_score"] = 4
    score_set["opponent_score"] = 4
    score_set["match_id"] = last_place_matches[0]["match_id"]

    submitted_scores_1 = league_model.process_player_score_report(league_bottom["user_id"], score_set)
    assert submitted_scores_1["message"]["match_status"] == "pending_approval"

    # Check that two users submitting scores changes score status to approved

    if last_place_matches[0]["user_1_id"] == league_bottom["user_id"]:
        other_user = last_place_matches[0]["user_2_id"]

    else:
        other_user = last_place_matches[0]["user_1_id"]

    submitted_scores_2 = league_model.process_player_score_report(other_user, score_set)
    assert submitted_scores_2["message"]["match_status"] == "approved"

    # Check that comparing a player to himself produces no head to head matches


    assert league_model.get_player_comparison(
            test_league["league_id"], league_top["user_id"],
             league_top["user_id"])["message"]["head_to_head"] == []

    

    with pytest.raises(exception.TigerLeaguesException):
        league_model.get_players_league_stats(test_league["league_id"], -1, matches=None, k=5)



        

