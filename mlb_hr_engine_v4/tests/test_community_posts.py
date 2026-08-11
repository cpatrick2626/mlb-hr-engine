"""Phase 1 community-slip contract tests; all storage is an in-memory fake."""

from __future__ import annotations

import copy
import unittest
from types import SimpleNamespace
from unittest import mock

from fastapi.testclient import TestClient


class _Query:
    def __init__(self, db, table):
        self.db, self.table, self.filters = db, table, []
        self.payload = None

    def select(self, _columns): return self
    def eq(self, field, value): self.filters.append((field, value)); return self
    def in_(self, field, values): self.filters.append((field, set(values))); return self
    def order(self, *_args, **_kwargs): return self
    def limit(self, *_args): return self
    def insert(self, payload): self.payload = payload; return self
    def update(self, payload): self.payload = payload; return self

    def execute(self):
        rows = self.db.rows[self.table]
        def matches(row):
            return all(
                row.get(field) == value if not isinstance(value, set) else row.get(field) in value
                for field, value in self.filters
            )
        matching = [row for row in rows if matches(row)]
        if self.payload is not None and self.table == "community_posts" and "post_id" not in self.payload:
            row = {**self.payload, "post_id": "post-1", "posted_at": "2026-08-11T12:00:00Z"}
            rows.append(row)
            return SimpleNamespace(data=[copy.deepcopy(row)])
        if self.payload is not None:
            for row in matching:
                row.update(self.payload)
            return SimpleNamespace(data=copy.deepcopy(matching))
        return SimpleNamespace(data=copy.deepcopy(matching))


class _Db:
    def __init__(self):
        self.rows = {
            "profiles": [
                {"user_id": "user-a", "app_number": 1, "username": "Alpha"},
                {"user_id": "user-b", "app_number": 2, "username": "Bravo"},
            ],
            "tickets": [
                {
                    "ticket_id": "ticket-a", "user_id": "user-a", "completed_at": "2026-08-11T11:00:00Z",
                    "fd_deployed": True, "odds_american": 700, "legs": [
                        {"leg_id": "leg-a", "player_name": "Player A", "model_prob": 0.2,
                         "market_odds_american": 450, "removed": False},
                    ],
                },
                {"ticket_id": "ticket-b", "user_id": "user-b", "completed_at": "2026-08-11T11:00:00Z", "fd_deployed": True},
            ],
            "community_posts": [],
        }

    def table(self, name): return _Query(self, name)


class CommunityPostsContractTests(unittest.TestCase):
    def setUp(self):
        from api import main as api_main
        from api.auth import require_auth
        self.api_main, self.require_auth, self.db = api_main, require_auth, _Db()

    def tearDown(self):
        self.api_main.app.dependency_overrides.clear()

    def _client_for(self, user_id):
        self.api_main.app.dependency_overrides[self.require_auth] = lambda: {"sub": user_id}
        return TestClient(self.api_main.app)

    def test_post_and_feed_are_auth_gated(self):
        client = TestClient(self.api_main.app)
        self.assertEqual(client.post("/api/community/posts", json={"ticket_id": "ticket-a"}).status_code, 401)
        self.assertEqual(client.get("/api/community/posts").status_code, 401)

    def test_owner_can_post_and_feed_groups_by_stable_user_not_mutable_username(self):
        with mock.patch.object(self.api_main, "supabase_client", return_value=self.db):
            post = self._client_for("user-a").post("/api/community/posts", json={"ticket_id": "ticket-a"})
            self.assertEqual(post.status_code, 200)
            self.assertNotIn("user_id", post.text)

            rename = self._client_for("user-a").patch(
                "/api/profile/username",
                json={"username": "Renamed User", "app_number": 999},
            )
            self.assertEqual(rename.status_code, 200)
            self.assertEqual(rename.json()["profile"]["app_number"], 1)

            feed = self._client_for("user-b").get("/api/community/posts")
        self.assertEqual(feed.status_code, 200)
        payload = feed.json()
        self.assertEqual(payload["users"][0]["username"], "Renamed User")
        self.assertEqual(payload["users"][0]["app_number"], 1)
        self.assertEqual(payload["users"][0]["posts"][0]["slip"]["ticket_id"], "ticket-a")
        self.assertEqual(payload["users"][0]["posts"][0]["slip"]["legs"][0]["market_odds_american"], 450)
        self.assertNotIn("user_id", str(payload))
        self.assertNotIn("email", str(payload).lower())

    def test_username_validation_rejects_invalid_values(self):
        with mock.patch.object(self.api_main, "supabase_client", return_value=self.db):
            response = self._client_for("user-a").patch("/api/profile/username", json={"username": "x"})
        self.assertEqual(response.status_code, 422)

    def test_caller_cannot_publish_another_users_ticket(self):
        with mock.patch.object(self.api_main, "supabase_client", return_value=self.db):
            response = self._client_for("user-a").post("/api/community/posts", json={"ticket_id": "ticket-b"})
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
