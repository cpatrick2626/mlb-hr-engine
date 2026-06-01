"""Weather client resiliency tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from clients import weather


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class TestWeatherGuard(unittest.TestCase):
    def setUp(self) -> None:
        weather._CACHE.clear()
        weather._DEGRADED_CACHE.clear()

    def test_success_response_is_cached_and_marked_fresh(self) -> None:
        payload = {
            "hourly": {
                "temperature_2m": [60.0, 61.0, 62.0, 63.0, 64.0, 65.0, 66.0, 67.0, 68.0, 69.0,
                                    70.0, 71.0, 72.0, 73.0, 74.0, 75.0, 76.0, 77.0, 78.0, 79.0],
                "windspeed_10m": [1.0] * 20,
                "winddirection_10m": [90.0] * 20,
                "relativehumidity_2m": [50] * 20,
            }
        }
        fake_response = _FakeResponse(payload)

        with mock.patch.object(weather._SESSION, "get", return_value=fake_response) as get_mock:
            result_1 = weather.get_game_weather(33.9416, -118.4085, 19)
            result_2 = weather.get_game_weather(33.9416, -118.4085, 19)

        self.assertEqual(get_mock.call_count, 1)
        self.assertEqual(result_1, result_2)
        self.assertEqual(result_1["weather_trust"], "fresh")
        self.assertFalse(result_1["weather_degraded"])
        self.assertEqual(result_1["temp_f"], 79.0)

    def test_failure_sets_degraded_cooldown_and_prevents_retry_storm(self) -> None:
        with mock.patch.object(weather._SESSION, "get", side_effect=RuntimeError("boom")) as get_mock:
            result_1 = weather.get_game_weather(40.7128, -74.0060, 19)
            result_2 = weather.get_game_weather(40.7128, -74.0060, 19)

        self.assertEqual(get_mock.call_count, 1)
        self.assertEqual(result_1, result_2)
        self.assertEqual(result_1["temp_f"], 70.0)
        self.assertEqual(result_1["wind_mph"], 0.0)
        self.assertEqual(result_1["humidity_pct"], 55)
        self.assertEqual(result_1["weather_trust"], "degraded")
        self.assertTrue(result_1["weather_degraded"])


if __name__ == "__main__":
    unittest.main()
