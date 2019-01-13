"""
test_league_simulation.py
"""

import sys
sys.path.insert(0, "../..")

from dev_scripts import simulate_users as sim
from tiger_leagues.models import db_model, league_model

db = db_model.Database()

def test_simulation(cleanup):
    # Check that many users can be added
    fake_users = sim.register_fake_users(num_users=10)
    num_fake_users = db.execute("SELECT COUNT (DISTINCT user_id) FROM users;").fetchone()["count"]
    assert num_fake_users == 10

    admin_user = fake_users[0]
    fake_users = fake_users[1:]

    league_info_list = sim.create_leagues(admin_user, num_leagues=1)
    num_leagues = db.execute("SELECT COUNT (league_id) FROM league_info;").fetchone()["count"]
    assert num_leagues == len(league_info_list)

    league_status = db.execute(
        "SELECT league_status FROM league_info WHERE league_id = %s",
        values=[league_info_list[0]["league_id"]]
    ).fetchone()["league_status"]
    assert league_status == league_model.LEAGUE_STAGE_ACCEPTING_USERS

    sim.populate_leagues(league_info_list, fake_users)
    assert sim.generate_matches(league_info_list)
