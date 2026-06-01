"""
Calibration drift monitor — Session 26.

Scans settled picks for systematic model bias across multiple dimensions.
Computes bucket-level, barrel-tier, archetype, odds-range, and sportsbook bias.
Returns structured alerts when bias exceeds configurable thresholds.

Alert levels:
  INFO     : |bias| > WARN_PP  at n >= N_WARN   (watch, may need action soon)
  WARNING  : |bias| > ALERT_PP at n >= N_ALERT   (needs attention)
  CRITICAL : |bias| > CRIT_PP  at n >= N_CRIT    (immediate re-calibration)

Usage:
  from tracking.drift_monitor import DriftMonitor
  dm = DriftMonitor()
  report = dm.run()
  for alert in report["alerts"]:
      print(alert)
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Optional


# ── Default alert thresholds ──────────────────────────────────────────────────
_DEFAULTS = {
    # Minimum n per segment before alerting (avoids false alarms on tiny samples)
    "N_CRIT":    20,    # n >= 20 for CRITICAL to fire
    "N_ALERT":   30,    # n >= 30 for WARNING to fire
    "N_WARN":    50,    # n >= 50 for INFO to fire
    # Bias magnitude thresholds (percentage points)
    "CRIT_PP":    5.0,  # |bias| > 5pp → CRITICAL
    "ALERT_PP":   3.0,  # |bias| > 3pp → WARNING
    "WARN_PP":    2.0,  # |bias| > 2pp → INFO
    # Rolling window thresholds (tighter because recent drift matters more)
    "ROLLING_DAYS":    30,
    "ROLLING_CRIT_PP": 4.0,
    "ROLLING_ALERT_PP":2.5,
}


class DriftMonitor:
    """Multi-dimensional calibration drift detector."""

    def __init__(self, thresholds: Optional[dict] = None):
        cfg = dict(_DEFAULTS)
        if thresholds:
            cfg.update(thresholds)
        self.cfg = cfg

    def run(self, rows: Optional[list[dict]] = None) -> dict:
        """
        Run full drift analysis.

        Args:
            rows: pre-loaded settled pick rows. If None, loads from pick_tracker.csv + results.csv.

        Returns:
            dict with keys: alerts, dimensions, summary, overall_bias, status
        """
        if rows is None:
            rows = _load_settled()

        if not rows:
            return {
                "alerts": [],
                "dimensions": {},
                "summary": "No settled picks to analyze.",
                "overall_bias": None,
                "status": "NO_DATA",
                "n_settled": 0,
            }

        all_alerts: list[dict] = []
        dimensions: dict[str, list[dict]] = {}

        # ── Overall bias ─────────────────────────────────────────────────────
        overall = _bucket_stats(rows, lambda r: "overall")
        overall_bias = overall["overall"]["bias_pp"] if "overall" in overall else None
        dimensions["overall"] = list(overall.values())

        # ── Probability bucket ────────────────────────────────────────────────
        def prob_bucket(r):
            try:
                p = float(r.get("model_prob_pct", 0) or 0)
            except (ValueError, TypeError):
                return None
            if p < 6:    return "<6%"
            if p < 8:    return "6-8%"
            if p < 10:   return "8-10%"
            if p < 12:   return "10-12%"
            if p < 15:   return "12-15%"
            if p < 20:   return "15-20%"
            return "20%+"

        bucket_stats = _bucket_stats(rows, prob_bucket)
        dimensions["prob_bucket"] = list(bucket_stats.values())
        all_alerts.extend(self._check_dimension(bucket_stats, "prob_bucket"))

        # ── Barrel tier ────────────────────────────────────────────────────────
        def barrel_tier(r):
            try:
                b = float(r.get("barrel_pct", 0) or 0)
            except (ValueError, TypeError):
                return None
            if b < 4:    return "barrel<4%"
            if b < 6:    return "barrel 4-6%"
            if b < 8:    return "barrel 6-8%"
            if b < 10:   return "barrel 8-10%"
            if b < 12:   return "barrel 10-12%"
            return "barrel 12%+"

        barrel_stats = _bucket_stats(rows, barrel_tier)
        dimensions["barrel_tier"] = list(barrel_stats.values())
        all_alerts.extend(self._check_dimension(barrel_stats, "barrel_tier"))

        # ── Hitter archetype ──────────────────────────────────────────────────
        def archetype(r):
            try:
                b  = float(r.get("barrel_pct", 0) or 0) / 100.0
                fb = float(r.get("pitcher_factor", 1) or 1)
            except (ValueError, TypeError):
                return None
            # Use barrel_pct as primary signal (more discriminating than pitcher_factor)
            if b >= 0.09:   return "Elite (barrel≥9%)"
            if b >= 0.07:   return "Power (barrel 7-9%)"
            if b >= 0.04:   return "Average (barrel 4-7%)"
            return "Contact (barrel<4%)"

        arch_stats = _bucket_stats(rows, archetype)
        dimensions["archetype"] = list(arch_stats.values())
        all_alerts.extend(self._check_dimension(arch_stats, "archetype"))

        # ── Odds range ────────────────────────────────────────────────────────
        def odds_range(r):
            try:
                odds = int(float(r.get("american_odds", 0) or 0))
            except (ValueError, TypeError):
                return None
            if odds <= 0:   return None
            if odds < 300:  return "+100-299"
            if odds < 500:  return "+300-499"
            if odds < 700:  return "+500-699"
            if odds < 1000: return "+700-999"
            return "+1000+"

        odds_stats = _bucket_stats(rows, odds_range)
        dimensions["odds_range"] = list(odds_stats.values())
        all_alerts.extend(self._check_dimension(odds_stats, "odds_range"))

        # ── Sportsbook ────────────────────────────────────────────────────────
        def book_key(r):
            b = r.get("sportsbook", "").strip()
            return b if b else None

        book_stats = _bucket_stats(rows, book_key)
        dimensions["sportsbook"] = list(book_stats.values())
        all_alerts.extend(self._check_dimension(book_stats, "sportsbook"))

        # ── Handedness ────────────────────────────────────────────────────────
        def handedness(r):
            s = r.get("source_section", "").strip()
            if "LHP" in s.upper():  return "vs LHP"
            if "RHP" in s.upper():  return "vs RHP"
            return None  # can't determine — skip

        hand_stats = _bucket_stats(rows, handedness)
        dimensions["handedness"] = list(hand_stats.values())
        all_alerts.extend(self._check_dimension(hand_stats, "handedness"))

        # ── Park factor tier ──────────────────────────────────────────────────
        def park_tier(r):
            try:
                pf = float(r.get("park_factor", 1) or 1)
            except (ValueError, TypeError):
                return None
            if pf >= 1.10:   return "Hitter park (≥1.10)"
            if pf >= 0.97:   return "Neutral park"
            return "Pitcher park (<0.97)"

        park_stats = _bucket_stats(rows, park_tier)
        dimensions["park_tier"] = list(park_stats.values())
        all_alerts.extend(self._check_dimension(park_stats, "park_tier"))

        # ── Weather tier ─────────────────────────────────────────────────────
        def weather_tier(r):
            try:
                wf = float(r.get("weather_factor", 1) or 1)
            except (ValueError, TypeError):
                return None
            if wf >= 1.05:   return "Hot/wind-aided (≥1.05)"
            if wf >= 0.95:   return "Neutral"
            return "Cold/suppressed (<0.95)"

        wx_stats = _bucket_stats(rows, weather_tier)
        dimensions["weather_tier"] = list(wx_stats.values())
        # Weather segment usually noisy — use looser threshold
        all_alerts.extend(self._check_dimension(wx_stats, "weather_tier",
                                                  alert_mult=1.5))

        # ── Rolling 30-day bias ───────────────────────────────────────────────
        rolling = _rolling_bias(rows, self.cfg["ROLLING_DAYS"])
        dimensions["rolling"] = rolling["buckets"]
        all_alerts.extend(self._check_rolling(rolling))

        # ── Dedup and sort alerts ─────────────────────────────────────────────
        all_alerts = sorted(all_alerts, key=lambda a: _LEVEL_ORDER.get(a["level"], 0), reverse=True)

        # ── Summary ───────────────────────────────────────────────────────────
        n_crit  = sum(1 for a in all_alerts if a["level"] == "CRITICAL")
        n_warn  = sum(1 for a in all_alerts if a["level"] == "WARNING")
        n_info  = sum(1 for a in all_alerts if a["level"] == "INFO")

        if n_crit > 0:
            status = "CRITICAL"
        elif n_warn > 0:
            status = "WARNING"
        elif n_info > 0:
            status = "INFO"
        else:
            status = "STABLE"

        overall_bias_str = f"{overall_bias:+.2f}pp" if overall_bias is not None else "n/a"
        summary = (
            f"Status: {status} | n={len(rows)} settled | "
            f"Overall bias={overall_bias_str} | "
            f"Alerts: {n_crit} CRITICAL, {n_warn} WARNING, {n_info} INFO"
        )

        return {
            "alerts":       all_alerts,
            "dimensions":   dimensions,
            "summary":      summary,
            "overall_bias": overall_bias,
            "status":       status,
            "n_settled":    len(rows),
            "n_crit":       n_crit,
            "n_warn":       n_warn,
            "n_info":       n_info,
        }

    def _check_dimension(
        self,
        stats: dict[str, dict],
        dim_name: str,
        alert_mult: float = 1.0,
    ) -> list[dict]:
        alerts = []
        for key, s in stats.items():
            n    = s["n"]
            bias = s["bias_pp"]
            abs_bias = abs(bias)
            level = None

            crit  = self.cfg["CRIT_PP"]  * alert_mult
            alert = self.cfg["ALERT_PP"] * alert_mult
            warn  = self.cfg["WARN_PP"]  * alert_mult

            if   abs_bias > crit  and n >= self.cfg["N_CRIT"]:
                level = "CRITICAL"
            elif abs_bias > alert and n >= self.cfg["N_ALERT"]:
                level = "WARNING"
            elif abs_bias > warn  and n >= self.cfg["N_WARN"]:
                level = "INFO"

            if level:
                dir_str = "over-predicts" if bias > 0 else "under-predicts"
                alerts.append({
                    "level":    level,
                    "dim":      dim_name,
                    "segment":  key,
                    "n":        n,
                    "bias_pp":  round(bias, 2),
                    "message":  (
                        f"[{level}] {dim_name}={key}: model {dir_str} by "
                        f"{abs_bias:.1f}pp (n={n}, actual={s['actual_pct']:.1f}%, "
                        f"model={s['model_pct']:.1f}%)"
                    ),
                })
        return alerts

    def _check_rolling(self, rolling: dict) -> list[dict]:
        alerts = []
        for bkt in rolling["buckets"]:
            n    = bkt["n"]
            bias = bkt["bias_pp"]
            abs_bias = abs(bias)

            if abs_bias > self.cfg["ROLLING_CRIT_PP"] and n >= self.cfg["N_CRIT"]:
                level = "CRITICAL"
            elif abs_bias > self.cfg["ROLLING_ALERT_PP"] and n >= self.cfg["N_ALERT"]:
                level = "WARNING"
            else:
                continue

            dir_str = "over-predicts" if bias > 0 else "under-predicts"
            alerts.append({
                "level":    level,
                "dim":      "rolling_30d",
                "segment":  bkt["segment"],
                "n":        n,
                "bias_pp":  round(bias, 2),
                "message":  (
                    f"[{level}] rolling_30d={bkt['segment']}: model {dir_str} by "
                    f"{abs_bias:.1f}pp (n={n})"
                ),
            })
        return alerts


# ── Module-level convenience function ────────────────────────────────────────

def run_drift_check(rows: Optional[list[dict]] = None, verbose: bool = True) -> dict:
    """
    Run drift check with default thresholds. Convenience wrapper.
    Prints summary to stdout when verbose=True.
    """
    dm = DriftMonitor()
    report = dm.run(rows)
    if verbose:
        print(f"\n{'='*70}")
        print("  CALIBRATION DRIFT MONITOR")
        print(f"{'='*70}")
        print(f"  {report['summary']}")
        if report["alerts"]:
            print()
            for a in report["alerts"]:
                print(f"  {a['message']}")
        else:
            print("  No drift alerts. Calibration is stable.")
        print(f"{'='*70}\n")
    return report


# ── Internal helpers ──────────────────────────────────────────────────────────

_LEVEL_ORDER = {"CRITICAL": 3, "WARNING": 2, "INFO": 1}


def _load_settled() -> list[dict]:
    """Load settled rows from pick_tracker.csv + results.csv."""
    rows: list[dict] = []
    try:
        from pathlib import Path
        import csv as _csv
        pt = Path(__file__).parent / "pick_tracker.csv"
        if pt.exists():
            with open(pt, newline="", encoding="utf-8") as f:
                for r in _csv.DictReader(f):
                    if r.get("hr_result") in ("0", "1"):
                        rows.append(r)
        rt = Path(__file__).parent / "results.csv"
        if rt.exists():
            with open(rt, newline="", encoding="utf-8") as f:
                for r in _csv.DictReader(f):
                    if r.get("hr_result") in ("0", "1"):
                        rows.append(r)
    except Exception as e:
        print(f"[drift_monitor] load error: {e}")
    return rows


def _safe_float(val, default=0.0) -> float:
    try:
        return float(val) if val and str(val).strip() not in ("", "--") else default
    except (ValueError, TypeError):
        return default


def _bucket_stats(rows: list[dict], key_fn) -> dict[str, dict]:
    """Aggregate actual HR% vs model_prob% by key_fn(row)."""
    agg: dict[str, dict] = defaultdict(lambda: {"n": 0, "hits": 0, "model_sum": 0.0})
    for r in rows:
        if r.get("hr_result") not in ("0", "1"):
            continue
        key = key_fn(r)
        if key is None:
            continue
        agg[key]["n"]         += 1
        agg[key]["hits"]      += 1 if r.get("hr_result") == "1" else 0
        agg[key]["model_sum"] += _safe_float(r.get("model_prob_pct", 0)) / 100.0

    result: dict[str, dict] = {}
    for key, a in agg.items():
        n = a["n"]
        if n == 0:
            continue
        actual_rate = a["hits"] / n
        model_rate  = a["model_sum"] / n
        # bias_pp: positive = model over-predicts (predicts higher than actual)
        result[key] = {
            "segment":    key,
            "n":          n,
            "hits":       a["hits"],
            "actual_pct": round(actual_rate * 100, 2),
            "model_pct":  round(model_rate * 100, 2),
            "bias_pp":    round((model_rate - actual_rate) * 100, 2),
        }
    return result


def _rolling_bias(rows: list[dict], days: int) -> dict:
    """Compute bias for the most recent N days across prob buckets."""
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    recent = [r for r in rows if r.get("date", "") >= cutoff]

    buckets_raw = _bucket_stats(recent, lambda r: _prob_bucket_label(r))
    buckets = sorted(buckets_raw.values(), key=lambda x: x["segment"])
    n_total = sum(b["n"] for b in buckets)

    return {
        "days":    days,
        "n_total": n_total,
        "buckets": buckets,
    }


def _prob_bucket_label(r) -> Optional[str]:
    try:
        p = float(r.get("model_prob_pct", 0) or 0)
    except (ValueError, TypeError):
        return None
    if p < 6:    return "<6%"
    if p < 10:   return "6-10%"
    if p < 15:   return "10-15%"
    if p < 20:   return "15-20%"
    return "20%+"
