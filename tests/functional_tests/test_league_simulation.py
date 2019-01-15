"""
test_league_simulation.py
"""

import sys
sys.path.insert(0, "../..")

from dev_scripts import simulate_tiger_leagues as sim
from tiger_leagues.models import db_model, league_model

db = db_model.Database()

def test_simulation(cleanup):
    # Check that many users can be added
    fake_users = sim.register_fake_users(num_users=10)
    num_fake_users = db.execute(
        "SELECT COUNT (DISTINCT user_id) FROM users;"
    ).fetchone()["count"]
    assert num_fake_users == 10

    admin_user = fake_users[0]
    fake_users = fake_users[1:]

    league_info = sim.create_league(admin_user)
    num_leagues = db.execute(
        "SELECT COUNT (league_id) FROM league_info;"
    ).fetchone()["count"]
    assert num_leagues == 1

    league_status = db.execute(
        "SELECT league_status FROM league_info WHERE league_id = %s",
        values=[league_info["league_id"]]
    ).fetchone()["league_status"]
    assert league_status == league_model.LEAGUE_STAGE_ACCEPTING_USERS

    sim.enroll_members(league_info, fake_users)
    league_info["num_active_players"] = len(fake_users) + 1
    sim.generate_divisions_and_fixtures(league_info)
