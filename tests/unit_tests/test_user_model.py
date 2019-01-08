"""
test_user_model.py
"""

import sys
sys.path.insert(0, "../..")

from tiger_leagues.models import user_model

test_profile = {"name": "Test", "room": "Blair A43"}

def test_valid_user_registration(cleanup):
    saved_profile = user_model.update_user_profile(
        None, "test_netid", test_profile
    )
    assert saved_profile["net_id"] == "test_netid"

def test_user_update(cleanup):
    returned_profile = user_model.update_user_profile(
        None, "test_netid", test_profile
    )
    old_profile = user_model.get_user("test_netid")
    assert returned_profile["user_id"] == old_profile["user_id"]

    updated_profile = user_model.update_user_profile(
        old_profile, "test_netid", {"name": "Test New Name"}
    )

    assert updated_profile["user_id"] == old_profile["user_id"]
    assert updated_profile["name"] == "Test New Name"
