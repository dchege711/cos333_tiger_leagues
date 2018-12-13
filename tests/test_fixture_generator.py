"""
test_fixture_generator.py

Sanity tests the fixture generation algorithm.

"""

import sys
sys.path.insert(0, "..")

from tiger_leagues.models import admin_model

def test_fixture_generator():
    """
    Asserts that the fixtures generated by the fixture generator module include 
    every possible match in a feasible schedule.

    @raises ValueError if the generated fixtures do not meet the criteria.
    """

    def check_fixtures(players):
        """
        @param List `players` a list of unique player IDs
        @raises AssertionError if the generated fixtures do not meet the criteria.
        """
        players_set = set(players)
        N = len(players)
        assert len(players_set) == N, "{} is not a list of unique items".format(str(players))

        fixtures = admin_model.fixture_generator(players)
        # for fixture in fixtures: print(fixture)
        expected_games = N - 1 if N > 1 else N
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
                
            if not_yet_played:
                raise ValueError(
                    "{} are missing games in {}".format(
                        str(not_yet_played), str(current_matches)
                    )
                )

    print("Testing an odd-length list:", end=" ")
    check_fixtures(list(range(9)))
    print("PASSED!")

    print("Testing an even-length list:", end=" ")
    check_fixtures(list(range(10)))
    print("PASSED!")

    print("Testing an empty list:", end=" ")
    check_fixtures([])
    print("PASSED")

    print("Testing a 2-element list:", end=" ")
    check_fixtures([0, 1])
    print("PASSED")

    print("Testing a 3-element list:", end=" ")
    check_fixtures([0, 1, 2])
    print("PASSED")

    print("Testing a 1-element list:", end=" ")
    check_fixtures([0])
    print("PASSED")

if __name__ == "__main__":
    test_fixture_generator()
