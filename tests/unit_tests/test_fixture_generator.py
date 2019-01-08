"""
test_fixture_generator.py

Sanity tests the fixture generation algorithm.

"""

import sys
sys.path.insert(0, "..")

from tiger_leagues.models import admin_model

def check_fixtures(players):
    """
    :param players: list 
    
    A list of unique player IDs
    
    :raise: ``AssertionError`` 
    
    If the generated fixtures do not meet the criteria.

    :return: ``bool``

    ``True`` if the fixtures meet all the criteria
    """
    players_set = set(players)
    N = len(players)
    assert len(players_set) == N, "{} is not a list of unique items".format(str(players))

    fixtures = admin_model.fixture_generator(players)
    # for fixture in fixtures: print(fixture)
    expected_games = N - 1 if N >= 1 else N
    assert len(fixtures) == expected_games, "Expected {} sets of games; received {}".format(expected_games, len(fixtures))

    not_yet_played = set()
    for current_matches in fixtures:
        not_yet_played = players_set.copy()

        def __check_player(player_id, matches):
            if player_id is None: return
            if player_id in not_yet_played:
                not_yet_played.remove(player_id)
            else:
                raise AssertionError(
                    "Invalid pairing for {}: {}".format(player_id, str(matches))
                )

        for player_a, player_b in current_matches:
            __check_player(player_a, current_matches)
            __check_player(player_b, current_matches)
            
        # If there's an odd number of players, one of them will not have a game
        if not_yet_played and not (N % 2 == 1 and len(not_yet_played) == 1):
            raise ValueError(
                "{} are missing games in {}".format(
                    str(not_yet_played), str(current_matches)
                )
            )
    
    return True

def test_odd_num_players():
    assert check_fixtures(list(range(9)))

def test_even_num_players():
    assert check_fixtures(list(range(10)))

def test_zero_players():
    assert check_fixtures([])

def test_two_players():
    assert check_fixtures([0, 1])

def test_three_players():
    assert check_fixtures([0, 1, 2])

def test_single_player():
    assert check_fixtures([0])
