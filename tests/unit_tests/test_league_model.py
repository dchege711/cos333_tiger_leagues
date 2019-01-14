"""
test_user_model.py
"""

import sys
from math import inf
from random import randint
from datetime import date, timedelta

import pytest

sys.path.insert(0, "../..")
from tiger_leagues.models import league_model, db_model, admin_model, exception
from tiger_leagues.models.exception import TigerLeaguesException
from dev_scripts import simulate_tiger_leagues as sim

db = db_model.Database()

def create_and_play_league(num_players=20):
    fake_users = sim.register_fake_users(num_users=num_players)
    num_fake_users = db.execute(
        "SELECT COUNT (DISTINCT user_id) FROM users;"
    ).fetchone()["count"]
    assert num_fake_users == num_players

    admin_user = fake_users[0]
    fake_users = fake_users[1:]

    fake_league = sim.create_league(admin_user)
    
    sim.enroll_members(fake_league, fake_users)
    fake_league["num_active_players"] = len(fake_users) + 1
    sim.generate_divisions_and_fixtures(fake_league)

    cursor = db.execute("SELECT match_id FROM match_info;")
    for row in cursor:
        admin_model.approve_match({
            "score_user_1": randint(0, 5), "score_user_2": randint(0, 5),
            "match_id": row["match_id"]
        }, admin_user["user_id"])

    return fake_league, fake_users, admin_user

def test_league_standings(cleanup):
    test_league, fake_users, admin_user = create_and_play_league()

    # Change scores to take a player to the top of their divison
    # Change scores to take a player to the bottom of their division

    league_top = fake_users[1]
    league_bottom = fake_users[2]

    leader_matches = league_model.get_players_current_matches(
        league_top["user_id"], test_league["league_id"],
        num_periods_before=inf, num_periods_after=inf
    )

    for match in leader_matches:
        if match["user_1_id"] == league_top["user_id"]:
            admin_model.approve_match({
                "score_user_1": 7, "score_user_2": 0,
                "match_id": match["match_id"]
            }, admin_user["user_id"])
        elif match["user_2_id"] == league_top["user_id"]:
            admin_model.approve_match({
                "score_user_1": 0, "score_user_2": 7,
                "match_id": match["match_id"]
            }, admin_user["user_id"])

    last_place_matches = league_model.get_players_current_matches(
        league_bottom["user_id"], test_league["league_id"],
        num_periods_before=inf, num_periods_after=inf
    )

    for match in last_place_matches:
        if match["user_1_id"] == league_bottom["user_id"]:
            admin_model.approve_match({
                "score_user_1": 0, "score_user_2": 9,
                "match_id": match["match_id"]
            }, admin_user["user_id"])
        elif match["user_2_id"] == league_bottom["user_id"]:
            admin_model.approve_match({
                "score_user_1": 9, "score_user_2": 0,
                "match_id": match["match_id"]
            }, admin_user["user_id"])

    # Check that the altered results have affected the league standings in 
    # the desired manner
    
    leader_info = league_model.get_players_league_stats(
        test_league["league_id"], league_top["user_id"], matches=None, k=5
    )

    leader_stats = leader_info["message"]
    assert leader_stats["rank"] == 1

    last_place_info = league_model.get_players_league_stats(
        test_league["league_id"], league_bottom["user_id"], matches=None, k=5
    )

    last_place_stats = last_place_info["message"]
    assert last_place_stats["rank"] == last_place_stats["lowest_rank"]

    ranking_on_table = league_model.get_league_standings(
        test_league["league_id"]
    )[last_place_stats["division_id"]][-1]
    assert ranking_on_table["user_id"] == last_place_stats["user_id"]

def test_league_standings_of_nonexistent_league(cleanup):
    assert league_model.get_league_standings(-1) == {}

def test_score_submission(cleanup):
    test_league, fake_users, _ = create_and_play_league()
    test_user = fake_users[-1]

    test_match = league_model.get_players_current_matches(
        test_user["user_id"], test_league["league_id"], 
        num_periods_before=inf, num_periods_after=inf
    )[0]

    # Check that submitting scores works
    score_set = {}
    score_set["my_score"] = 4
    score_set["opponent_score"] = 4
    score_set["match_id"] = test_match["match_id"]

    submitted_scores_1 = league_model.process_player_score_report(
        test_user["user_id"], score_set
    )
    assert submitted_scores_1["message"]["match_status"] == "pending_approval"

    # Check that two users submitting same scores changes score status to approved
    if test_match["user_1_id"] == test_user["user_id"]:
        other_user_id = test_match["user_2_id"]
    else:
        other_user_id = test_match["user_1_id"]

    submitted_scores_2 = league_model.process_player_score_report(
        other_user_id, score_set
    )
    assert submitted_scores_2["message"]["match_status"] == "approved"

def test_self_player_comparison_produces_single_stats(cleanup):
    test_league, fake_users, _ = create_and_play_league()
    test_user = fake_users[-1]

    # Check that comparing a player to himself produces no head to head matches
    assert league_model.get_player_comparison(
        test_league["league_id"], test_user["user_id"], str(test_user["user_id"])
    )["message"]["head_to_head"] == []

def test_fetching_stats_for_nonexistent_user(cleanup):
    test_league, _, _ = create_and_play_league()
    # Check that getting the stats for a non-existent player raises an exception
    with pytest.raises(exception.TigerLeaguesException):
        league_model.get_players_league_stats(
            test_league["league_id"], -1, matches=None, k=5
        )

base_league_info = {
    "league_name": "Dummy League", 
    "description": "Simulation builds character", 
    "points_per_win": 3, 
    "points_per_draw": 1,
    "points_per_loss": 0,
    "max_num_players": 10,
    "num_games_per_period": 1,
    "length_period_in_days": 5,
    "registration_deadline": (date.today()).isoformat(),
    "additional_questions": {
        "question0": {
            "question": "Do you own a basketball?",
            "options": "Yes, No"
        }
    }
}

def test_create_league_incomplete_form():
    base_league_info.pop("league_name")
    with pytest.raises(TigerLeaguesException):
        league_model.create_league(base_league_info, 1)
    base_league_info["league_name"] = "Dummy League"

def test_create_league_in_the_past():
    base_league_info["registration_deadline"] = (date.today() - timedelta(days=1)).isoformat()
    with pytest.raises(TigerLeaguesException):
        league_model.create_league(base_league_info, 1)
    base_league_info["registration_deadline"] = (date.today()).isoformat()
    