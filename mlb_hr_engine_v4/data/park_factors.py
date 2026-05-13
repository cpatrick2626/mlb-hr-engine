"""
MLB park HR factors and stadium geodata.

hr_factor       > 1.0 → hitter-friendly (neutral L/R average, legacy fallback)
hr_factor_L     — LHB-specific HR factor
hr_factor_R     — RHB-specific HR factor

Handedness splits derived from 2022-2025 multi-year handedness park factor data.
Symmetric parks set L == R == hr_factor. Asymmetric parks reflect known porch geometry:
  NYY short RF porch → large LHB boost
  BOS Green Monster → large RHB boost
  SF Oracle deep RF + marine air → severe LHB suppression
  HOU Crawford Boxes LF → RHB boost
  DET deep RF → LHB suppressed
  LAD/SD symmetric suppressors with slight LHB disadvantage

cf_bearing: compass direction FROM home plate TO center field (degrees, 0=N).
tz_offset:  UTC offset during MLB season (DST Apr–Oct for US/Canada; ARI never DST).
"""

PARK_FACTORS: dict[str, dict] = {
    "ARI": {"name": "Chase Field",                 "hr_factor": 1.06, "hr_factor_L": 1.06, "hr_factor_R": 1.06, "cf_bearing":  335, "lat": 33.4453, "lon": -112.0667, "tz_offset": -7},
    "ATL": {"name": "Truist Park",                 "hr_factor": 1.05, "hr_factor_L": 1.04, "hr_factor_R": 1.06, "cf_bearing":    5, "lat": 33.8908, "lon":  -84.4681, "tz_offset": -4},
    "BAL": {"name": "Oriole Park at Camden Yards",  "hr_factor": 1.06, "hr_factor_L": 1.05, "hr_factor_R": 1.07, "cf_bearing":  325, "lat": 39.2838, "lon":  -76.6216, "tz_offset": -4},
    "BOS": {"name": "Fenway Park",                 "hr_factor": 1.08, "hr_factor_L": 0.96, "hr_factor_R": 1.19, "cf_bearing":   70, "lat": 42.3467, "lon":  -71.0972, "tz_offset": -4},
    "CHC": {"name": "Wrigley Field",               "hr_factor": 1.00, "hr_factor_L": 1.00, "hr_factor_R": 1.00, "cf_bearing":   55, "lat": 41.9484, "lon":  -87.6554, "tz_offset": -5},
    "CWS": {"name": "Guaranteed Rate Field",       "hr_factor": 1.03, "hr_factor_L": 1.01, "hr_factor_R": 1.05, "cf_bearing":    0, "lat": 41.8300, "lon":  -87.6339, "tz_offset": -5},
    "CIN": {"name": "Great American Ball Park",    "hr_factor": 1.18, "hr_factor_L": 1.17, "hr_factor_R": 1.19, "cf_bearing":   10, "lat": 39.0975, "lon":  -84.5083, "tz_offset": -4},
    "CLE": {"name": "Progressive Field",           "hr_factor": 0.97, "hr_factor_L": 0.95, "hr_factor_R": 0.99, "cf_bearing":   30, "lat": 41.4958, "lon":  -81.6853, "tz_offset": -4},
    "COL": {"name": "Coors Field",                 "hr_factor": 1.28, "hr_factor_L": 1.28, "hr_factor_R": 1.28, "cf_bearing":  350, "lat": 39.7560, "lon": -104.9942, "tz_offset": -6},
    "DET": {"name": "Comerica Park",               "hr_factor": 0.93, "hr_factor_L": 0.88, "hr_factor_R": 0.98, "cf_bearing":  355, "lat": 42.3390, "lon":  -83.0485, "tz_offset": -4},
    "HOU": {"name": "Minute Maid Park",            "hr_factor": 1.10, "hr_factor_L": 1.05, "hr_factor_R": 1.15, "cf_bearing":    5, "lat": 29.7572, "lon":  -95.3555, "tz_offset": -5},
    "KC":  {"name": "Kauffman Stadium",            "hr_factor": 0.96, "hr_factor_L": 0.95, "hr_factor_R": 0.97, "cf_bearing":    0, "lat": 39.0517, "lon":  -94.4803, "tz_offset": -5},
    "LAA": {"name": "Angel Stadium",               "hr_factor": 0.97, "hr_factor_L": 0.95, "hr_factor_R": 0.99, "cf_bearing":  340, "lat": 33.8003, "lon": -117.8827, "tz_offset": -7},
    "LAD": {"name": "Dodger Stadium",              "hr_factor": 0.91, "hr_factor_L": 0.88, "hr_factor_R": 0.94, "cf_bearing":  355, "lat": 34.0739, "lon": -118.2400, "tz_offset": -7},
    "MIA": {"name": "loanDepot park",              "hr_factor": 1.02, "hr_factor_L": 1.01, "hr_factor_R": 1.03, "cf_bearing":  340, "lat": 25.7779, "lon":  -80.2197, "tz_offset": -4},
    "MIL": {"name": "American Family Field",       "hr_factor": 1.07, "hr_factor_L": 1.06, "hr_factor_R": 1.08, "cf_bearing":   10, "lat": 43.0280, "lon":  -87.9712, "tz_offset": -5},
    "MIN": {"name": "Target Field",                "hr_factor": 0.99, "hr_factor_L": 0.97, "hr_factor_R": 1.01, "cf_bearing":   15, "lat": 44.9817, "lon":  -93.2778, "tz_offset": -5},
    "NYM": {"name": "Citi Field",                  "hr_factor": 0.97, "hr_factor_L": 0.95, "hr_factor_R": 0.99, "cf_bearing":  355, "lat": 40.7571, "lon":  -73.8458, "tz_offset": -4},
    "NYY": {"name": "Yankee Stadium",              "hr_factor": 1.10, "hr_factor_L": 1.19, "hr_factor_R": 1.03, "cf_bearing":  355, "lat": 40.8296, "lon":  -73.9262, "tz_offset": -4},
    "ATH": {"name": "Sutter Health Park",          "hr_factor": 1.05, "hr_factor_L": 1.04, "hr_factor_R": 1.06, "cf_bearing":   10, "lat": 38.5726, "lon": -121.5041, "tz_offset": -7},
    "OAK": {"name": "Sutter Health Park",          "hr_factor": 1.05, "hr_factor_L": 1.04, "hr_factor_R": 1.06, "cf_bearing":   10, "lat": 38.5726, "lon": -121.5041, "tz_offset": -7},
    "PHI": {"name": "Citizens Bank Park",          "hr_factor": 1.11, "hr_factor_L": 1.09, "hr_factor_R": 1.13, "cf_bearing":   25, "lat": 39.9056, "lon":  -75.1665, "tz_offset": -4},
    "PIT": {"name": "PNC Park",                    "hr_factor": 1.04, "hr_factor_L": 1.02, "hr_factor_R": 1.06, "cf_bearing":  355, "lat": 40.4469, "lon":  -80.0057, "tz_offset": -4},
    "SD":  {"name": "Petco Park",                  "hr_factor": 0.89, "hr_factor_L": 0.85, "hr_factor_R": 0.93, "cf_bearing":  290, "lat": 32.7074, "lon": -117.1566, "tz_offset": -7},
    "SF":  {"name": "Oracle Park",                 "hr_factor": 0.83, "hr_factor_L": 0.75, "hr_factor_R": 0.91, "cf_bearing":  355, "lat": 37.7785, "lon": -122.3893, "tz_offset": -7},
    "SEA": {"name": "T-Mobile Park",               "hr_factor": 1.02, "hr_factor_L": 0.99, "hr_factor_R": 1.05, "cf_bearing":   10, "lat": 47.5914, "lon": -122.3325, "tz_offset": -7},
    "STL": {"name": "Busch Stadium",               "hr_factor": 1.03, "hr_factor_L": 1.01, "hr_factor_R": 1.05, "cf_bearing":    0, "lat": 38.6226, "lon":  -90.1929, "tz_offset": -5},
    "TB":  {"name": "Tropicana Field",             "hr_factor": 1.00, "hr_factor_L": 1.00, "hr_factor_R": 1.00, "cf_bearing":  340, "lat": 27.7683, "lon":  -82.6534, "tz_offset": -4},
    "TEX": {"name": "Globe Life Field",            "hr_factor": 1.12, "hr_factor_L": 1.09, "hr_factor_R": 1.15, "cf_bearing":  350, "lat": 32.7473, "lon":  -97.0827, "tz_offset": -5},
    "TOR": {"name": "Rogers Centre",               "hr_factor": 1.01, "hr_factor_L": 1.00, "hr_factor_R": 1.02, "cf_bearing":  350, "lat": 43.6414, "lon":  -79.3892, "tz_offset": -4},
    "WSH": {"name": "Nationals Park",              "hr_factor": 1.04, "hr_factor_L": 1.02, "hr_factor_R": 1.06, "cf_bearing":  350, "lat": 38.8730, "lon":  -77.0074, "tz_offset": -4},
}


def get_park(team_abbr: str) -> dict:
    return PARK_FACTORS.get(team_abbr.upper(), {
        "name": "Unknown Park", "hr_factor": 1.00,
        "hr_factor_L": 1.00, "hr_factor_R": 1.00,
        "lat": 39.5, "lon": -98.0,
    })


def get_park_hr_factor(team_abbr: str, batter_side: str) -> float:
    """
    Return handedness-adjusted park HR factor.
    batter_side: 'L', 'R', or 'S' (switch hitter uses average of L and R).
    Falls back to neutral hr_factor when handedness keys are absent.
    """
    park = get_park(team_abbr)
    side = (batter_side or "").upper()
    if side == "L":
        return park.get("hr_factor_L", park.get("hr_factor", 1.0))
    if side == "R":
        return park.get("hr_factor_R", park.get("hr_factor", 1.0))
    # Switch hitter: average the two sides
    l = park.get("hr_factor_L", park.get("hr_factor", 1.0))
    r = park.get("hr_factor_R", park.get("hr_factor", 1.0))
    return round((l + r) / 2.0, 3)


def park_label(team_abbr: str) -> str:
    p = get_park(team_abbr)
    f = p["hr_factor"]
    if f >= 1.10:
        return f"[bold green]{p['name']} ({f:.2f}x)[/bold green]"
    if f >= 1.04:
        return f"[green]{p['name']} ({f:.2f}x)[/green]"
    if f <= 0.90:
        return f"[bold red]{p['name']} ({f:.2f}x)[/bold red]"
    if f <= 0.96:
        return f"[red]{p['name']} ({f:.2f}x)[/red]"
    return f"{p['name']} ({f:.2f}x)"
