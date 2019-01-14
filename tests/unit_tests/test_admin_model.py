"""
test_admin_model.py
"""

import sys
sys.path.insert(0, "../..")
sys.path.insert(0, "../")

import pytest

from tiger_leagues.models import admin_model, league_model
from tiger_leagues.models.exception import TigerLeaguesException
from dev_scripts import simulate_users as sim

def test_input_validation_update_join_league_requests(cleanup):
    fake_user = sim.register_fake_users(num_users=1)[0]
    _ = sim.create_leagues(fake_user, num_leagues=1)[0]

    # Test non-existent statuses
    with pytest.raises(TigerLeaguesException):
        admin_model.update_join_league_requests(
            1, {1: "hahahahaha"}
        )

    # Test invalid user IDs
    with pytest.raises(TigerLeaguesException):
        admin_model.update_join_league_requests(
            1, {"fake_user_id": "member"}
        )

def test_user_cannot_be_added_without_consent(cleanup):
    fake_users = sim.register_fake_users(num_users=2)
    league_info_list = sim.create_leagues(fake_users[0], num_leagues=1)

    join_results = admin_model.update_join_league_requests(
        league_info_list[0]["league_id"],
        {
            fake_users[1]["user_id"]: league_model.STATUS_MEMBER
        }
    )["message"][fake_users[1]["user_id"]]
    assert join_results is None

def test_league_must_have_at_least_one_admin(cleanup):
    fake_user = sim.register_fake_users(num_users=1)[0]
    league_info = sim.create_leagues(fake_user, num_leagues=1)[0]
    
    with pytest.raises(TigerLeaguesException):
        admin_model.update_join_league_requests(
            league_info["league_id"],
            {fake_user["user_id"]: league_model.STATUS_MEMBER}
        )

    assert league_model.STATUS_ADMIN == admin_model.update_join_league_requests(
        league_info["league_id"],
        {fake_user["user_id"]: league_model.STATUS_ADMIN}
    )["message"][fake_user["user_id"]]
