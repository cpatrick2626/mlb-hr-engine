"""Runtime provenance tests for descriptive probability lineage."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if isinstance(sys.modules.get("tracking"), mock.Mock):
    for module_name in tuple(sys.modules):
        if module_name == "tracking" or module_name.startswith("tracking."):
            del sys.modules[module_name]

from tracking.runtime_provenance import build_runtime_provenance


class TestRuntimeProvenance(unittest.TestCase):
    def test_github_missing_artifact_records_identity_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "learned_adjustments.json"
            adaptive = SimpleNamespace(
                ADJUSTMENTS_PATH=missing,
                get=lambda key, default=None: 1.0 if key == "prob_scale" else default,
            )
            with mock.patch.dict(
                "os.environ",
                {
                    "GITHUB_ACTIONS": "true",
                    "GITHUB_EVENT_NAME": "schedule",
                    "GITHUB_SHA": "abc123",
                    "GITHUB_RUN_ID": "42",
                    "GITHUB_RUN_ATTEMPT": "2",
                },
                clear=True,
            ):
                provenance = build_runtime_provenance(adaptive)

        self.assertEqual(provenance["source_lane"], "github_scheduled_pipeline")
        self.assertEqual(provenance["git_sha"], "abc123")
        self.assertEqual(provenance["run_id"], "42:2")
        self.assertEqual(provenance["effective_prob_scale"], 1.0)
        self.assertEqual(provenance["adaptive_load_status"], "MISSING")
        self.assertEqual(provenance["adaptive_source_kind"], "default_missing_file")
        self.assertIsNone(provenance["adaptive_artifact_sha256"])
        self.assertTrue(provenance["calibration_fingerprint_sha256"])

    def test_fly_artifact_preserves_volume_value_and_image_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact = Path(temp_dir) / "learned_adjustments.json"
            payload = json.dumps({"prob_scale": 1.12}).encode("utf-8")
            artifact.write_bytes(payload)
            adaptive = SimpleNamespace(
                ADJUSTMENTS_PATH=artifact,
                get=lambda key, default=None: 1.12 if key == "prob_scale" else default,
            )
            with mock.patch.dict(
                "os.environ",
                {
                    "FLY_APP_NAME": "mlb-hr-api",
                    "FLY_IMAGE_REF": "registry.fly.io/mlb-hr-api:deployment-123",
                    "FLY_MACHINE_VERSION": "v9",
                    "FLY_MACHINE_ID": "machine-7",
                },
                clear=True,
            ):
                provenance = build_runtime_provenance(adaptive)

        self.assertEqual(provenance["source_lane"], "fly_generation")
        self.assertIsNone(provenance["git_sha"])
        self.assertEqual(
            provenance["image_identity"],
            "registry.fly.io/mlb-hr-api:deployment-123",
        )
        self.assertEqual(provenance["machine_version"], "v9")
        self.assertEqual(provenance["run_id"], "machine-7")
        self.assertEqual(provenance["effective_prob_scale"], 1.12)
        self.assertEqual(provenance["adaptive_load_status"], "LOADED")
        self.assertEqual(provenance["adaptive_source_kind"], "tracking_data_dir_file")
        self.assertEqual(
            provenance["adaptive_artifact_sha256"], hashlib.sha256(payload).hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
