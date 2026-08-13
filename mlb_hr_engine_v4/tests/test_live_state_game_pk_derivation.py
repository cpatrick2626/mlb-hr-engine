"""game_pk derivation tests for the Phase-1 live-alerts join (Layer 3).

legs rows don't store game_pk directly; api/ticket_history.py derives it by
joining leg.team + leg.leg_date against that day's schedule, reusing the
existing _match_game() doubleheader-safe join (same helper /api/my-tickets
already uses for game_status/linescore). Confirms: single-game -> game_pk
populated, and doubleheader-ambiguous (team+date matches 2+ games, opponent
doesn't disambiguate) -> game_pk is None so the client never polls/fires on
a guessed game.
"""

import unittest

from api.ticket_history import _clean_leg


def _game(game_pk, home, away):
    return {
        "gamePk": game_pk,
        "status": {"abstractGameState": "Live"},
        "teams": {
            "home": {"team": {"abbreviation": home}},
            "away": {"team": {"abbreviation": away}},
        },
    }


class GamePkDerivationTests(unittest.TestCase):
    def test_single_game_resolves_game_pk(self):
        leg = {"leg_date": "2026-08-13", "player_id": "660271", "team": "NYY", "opponent": "BOS"}
        schedules = {"2026-08-13": [_game(745123, home="BOS", away="NYY")]}

        clean = _clean_leg(leg, ticket_date=None, schedules=schedules)

        self.assertEqual(clean["game_pk"], 745123)
        self.assertEqual(clean["player_id"], "660271")

    def test_doubleheader_ambiguous_without_opponent_leaves_game_pk_none(self):
        """Same two teams play twice in one day; leg has no opponent on file."""
        leg = {"leg_date": "2026-08-13", "player_id": "660271", "team": "NYY", "opponent": None}
        schedules = {"2026-08-13": [
            _game(745123, home="BOS", away="NYY"),
            _game(745124, home="BOS", away="NYY"),
        ]}

        clean = _clean_leg(leg, ticket_date=None, schedules=schedules)

        self.assertIsNone(clean["game_pk"])

    def test_doubleheader_disambiguated_by_opponent_still_ambiguous_across_two_games(self):
        """Doubleheader: team+opponent match BOTH games (same two teams play twice).
        Opponent alone can't tell game 1 from game 2 -> stay silent, never guess."""
        leg = {"leg_date": "2026-08-13", "player_id": "660271", "team": "NYY", "opponent": "BOS"}
        schedules = {"2026-08-13": [
            _game(745123, home="BOS", away="NYY"),
            _game(745124, home="BOS", away="NYY"),
        ]}

        clean = _clean_leg(leg, ticket_date=None, schedules=schedules)

        self.assertIsNone(clean["game_pk"])

    def test_team_playing_two_different_opponents_same_day_resolves_via_opponent(self):
        """Not a doubleheader for this team — two unrelated games that day; the
        opponent field alone is enough to pick the right one unambiguously."""
        leg = {"leg_date": "2026-08-13", "player_id": "660271", "team": "NYY", "opponent": "BOS"}
        schedules = {"2026-08-13": [
            _game(745123, home="BOS", away="NYY"),
            _game(745125, home="TOR", away="SEA"),
        ]}

        clean = _clean_leg(leg, ticket_date=None, schedules=schedules)

        self.assertEqual(clean["game_pk"], 745123)

    def test_no_matching_game_leaves_game_pk_none(self):
        leg = {"leg_date": "2026-08-13", "player_id": "660271", "team": "NYY", "opponent": "BOS"}
        clean = _clean_leg(leg, ticket_date=None, schedules={"2026-08-13": []})
        self.assertIsNone(clean["game_pk"])


if __name__ == "__main__":
    unittest.main()
