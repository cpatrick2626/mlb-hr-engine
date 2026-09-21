"""Read-only runtime identity for prospective MAIN probability lineage."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import config


def _calibration_fingerprint() -> tuple[str, dict[str, Any]]:
    state = {
        "calibration_enabled": bool(getattr(config, "CALIBRATION_ENABLED", False)),
        "calibration_method": str(getattr(config, "CALIBRATION_METHOD", "none")),
        "calibration_platt_a": getattr(config, "CALIBRATION_PLATT_A", None),
        "calibration_platt_b": getattr(config, "CALIBRATION_PLATT_B", None),
        "calibration_isotonic_breakpoints": getattr(
            config, "CALIBRATION_ISOTONIC_BREAKPOINTS", []
        ),
        "calibration_isotonic_values": getattr(
            config, "CALIBRATION_ISOTONIC_VALUES", []
        ),
        "elite_platt_enabled": bool(getattr(config, "ELITE_PLATT_ENABLED", False)),
        "elite_platt_a": getattr(config, "ELITE_PLATT_A", None),
        "elite_platt_b": getattr(config, "ELITE_PLATT_B", None),
        "elite_platt_barrel_threshold": getattr(
            config, "ELITE_PLATT_BARREL_THRESHOLD", None
        ),
        "max_game_hr_prob": getattr(config, "MAX_GAME_HR_PROB", None),
        "warehouse_isotonic_enabled": bool(
            getattr(config, "WAREHOUSE_ISOTONIC_ENABLED", False)
        ),
    }
    encoded = json.dumps(
        state,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest(), state


def _artifact_identity(path: Path) -> dict[str, Any]:
    try:
        payload = path.read_bytes()
    except FileNotFoundError:
        return {
            "adaptive_artifact_sha256": None,
            "adaptive_load_status": "MISSING",
            "adaptive_source_kind": "default_missing_file",
        }
    except OSError:
        return {
            "adaptive_artifact_sha256": None,
            "adaptive_load_status": "UNREADABLE",
            "adaptive_source_kind": "default_unreadable_file",
        }

    try:
        decoded = json.loads(payload.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("artifact root is not an object")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        status = "INVALID"
    else:
        status = "LOADED"

    return {
        "adaptive_artifact_sha256": hashlib.sha256(payload).hexdigest(),
        "adaptive_load_status": status,
        "adaptive_source_kind": "tracking_data_dir_file",
    }


def _lane_identity() -> dict[str, str | None]:
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        event = os.environ.get("GITHUB_EVENT_NAME")
        lane = (
            "github_scheduled_pipeline"
            if event == "schedule"
            else "github_manual_pipeline"
        )
        run_id = os.environ.get("GITHUB_RUN_ID")
        attempt = os.environ.get("GITHUB_RUN_ATTEMPT")
        if run_id and attempt:
            run_id = f"{run_id}:{attempt}"
        return {
            "source_lane": lane,
            "source_trigger": event,
            "git_sha": os.environ.get("GITHUB_SHA"),
            "image_identity": None,
            "machine_version": None,
            "run_id": run_id,
        }

    if os.environ.get("FLY_APP_NAME"):
        return {
            "source_lane": "fly_generation",
            "source_trigger": "api_pipeline_run",
            "git_sha": os.environ.get("SOURCE_VERSION"),
            "image_identity": os.environ.get("FLY_IMAGE_REF"),
            "machine_version": os.environ.get("FLY_MACHINE_VERSION"),
            "run_id": os.environ.get("FLY_MACHINE_ID"),
        }

    return {
        "source_lane": "local_manual",
        "source_trigger": None,
        "git_sha": os.environ.get("SOURCE_VERSION"),
        "image_identity": None,
        "machine_version": None,
        "run_id": None,
    }


def build_runtime_provenance(adaptive_weights: Any) -> dict[str, Any]:
    """Describe the loaded adaptive value and calibration config without mutation."""
    path = Path(adaptive_weights.ADJUSTMENTS_PATH).resolve()
    effective_prob_scale = adaptive_weights.get("prob_scale", 1.0)
    calibration_hash, calibration_state = _calibration_fingerprint()
    return {
        "schema_version": 1,
        **_lane_identity(),
        "adaptive_artifact_path": str(path),
        **_artifact_identity(path),
        "effective_prob_scale": effective_prob_scale,
        "calibration_fingerprint_sha256": calibration_hash,
        "calibration_enabled": calibration_state["calibration_enabled"],
        "calibration_method": calibration_state["calibration_method"],
        "warehouse_isotonic_enabled": calibration_state[
            "warehouse_isotonic_enabled"
        ],
    }


def unavailable_adaptive_provenance() -> dict[str, Any]:
    """Describe the pipeline's existing identity behavior after import failure."""
    calibration_hash, calibration_state = _calibration_fingerprint()
    return {
        "schema_version": 1,
        **_lane_identity(),
        "adaptive_artifact_path": None,
        "adaptive_artifact_sha256": None,
        "adaptive_load_status": "IMPORT_UNAVAILABLE",
        "adaptive_source_kind": "import_unavailable_identity",
        "effective_prob_scale": 1.0,
        "calibration_fingerprint_sha256": calibration_hash,
        "calibration_enabled": calibration_state["calibration_enabled"],
        "calibration_method": calibration_state["calibration_method"],
        "warehouse_isotonic_enabled": calibration_state[
            "warehouse_isotonic_enabled"
        ],
    }
