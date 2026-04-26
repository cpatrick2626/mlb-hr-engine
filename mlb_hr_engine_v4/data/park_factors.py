"""
MLB park HR factors and stadium geodata.

hr_factor > 1.0 → hitter-friendly (more HRs than average)
hr_factor < 1.0 → pitcher-friendly (fewer HRs than average)

Derived from 2022-2024 multi-year park factor data (ESPN / FanGraphs).
Coordinates used for Open-Meteo weather lookups.
"""

# Keyed by MLB team abbreviation (home team = their park)
# cf_bearing: compass direction FROM home plate TO center field (degrees, 0=N, 90=E, 180=S, 270=W).
# Used by weather.wind_factor() to compute whether wind blows out to CF (tailwind)
# or in from CF (headwind). Dome parks have a bearing but it's irrelevant (wind disabled).
PARK_FACTORS: dict[str, dict] = {
    "ARI": {"name": "Chase Field",                "hr_factor": 1.06, "cf_bearing":  335, "lat": 33.4453, "lon": -112.0667},
    "ATL": {"name": "Truist Park",                "hr_factor": 1.05, "cf_bearing":    5, "lat": 33.8908, "lon": -84.4681},
    "BAL": {"name": "Oriole Park at Camden Yards", "hr_factor": 1.06, "cf_bearing":  325, "lat": 39.2838, "lon": -76.6216},
    "BOS": {"name": "Fenway Park",                "hr_factor": 1.08, "cf_bearing":   70, "lat": 42.3467, "lon": -71.0972},
    "CHC": {"name": "Wrigley Field",              "hr_factor": 1.00, "cf_bearing":   55, "lat": 41.9484, "lon": -87.6554},
    "CWS": {"name": "Guaranteed Rate Field",      "hr_factor": 1.03, "cf_bearing":    0, "lat": 41.8300, "lon": -87.6339},
    "CIN": {"name": "Great American Ball Park",   "hr_factor": 1.18, "cf_bearing":   10, "lat": 39.0975, "lon": -84.5083},
    "CLE": {"name": "Progressive Field",          "hr_factor": 0.97, "cf_bearing":   30, "lat": 41.4958, "lon": -81.6853},
    "COL": {"name": "Coors Field",                "hr_factor": 1.28, "cf_bearing":  350, "lat": 39.7560, "lon": -104.9942},
    "DET": {"name": "Comerica Park",              "hr_factor": 0.93, "cf_bearing":  355, "lat": 42.3390, "lon": -83.0485},
    "HOU": {"name": "Minute Maid Park",           "hr_factor": 1.10, "cf_bearing":    5, "lat": 29.7572, "lon": -95.3555},
    "KC":  {"name": "Kauffman Stadium",           "hr_factor": 0.96, "cf_bearing":    0, "lat": 39.0517, "lon": -94.4803},
    "LAA": {"name": "Angel Stadium",              "hr_factor": 0.97, "cf_bearing":  340, "lat": 33.8003, "lon": -117.8827},
    "LAD": {"name": "Dodger Stadium",             "hr_factor": 0.96, "cf_bearing":  355, "lat": 34.0739, "lon": -118.2400},
    "MIA": {"name": "loanDepot park",             "hr_factor": 1.02, "cf_bearing":  340, "lat": 25.7779, "lon": -80.2197},
    "MIL": {"name": "American Family Field",      "hr_factor": 1.07, "cf_bearing":   10, "lat": 43.0280, "lon": -87.9712},
    "MIN": {"name": "Target Field",               "hr_factor": 0.99, "cf_bearing":   15, "lat": 44.9817, "lon": -93.2778},
    "NYM": {"name": "Citi Field",                 "hr_factor": 0.97, "cf_bearing":  355, "lat": 40.7571, "lon": -73.8458},
    "NYY": {"name": "Yankee Stadium",             "hr_factor": 1.10, "cf_bearing":  355, "lat": 40.8296, "lon": -73.9262},
    "OAK": {"name": "Sutter Health Park",         "hr_factor": 0.97, "cf_bearing":   10, "lat": 38.5726, "lon": -121.5041},
    "PHI": {"name": "Citizens Bank Park",         "hr_factor": 1.11, "cf_bearing":   25, "lat": 39.9056, "lon": -75.1665},
    "PIT": {"name": "PNC Park",                   "hr_factor": 1.04, "cf_bearing":  355, "lat": 40.4469, "lon": -80.0057},
    "SD":  {"name": "Petco Park",                 "hr_factor": 0.89, "cf_bearing":  290, "lat": 32.7074, "lon": -117.1566},
    "SF":  {"name": "Oracle Park",                "hr_factor": 0.83, "cf_bearing":  355, "lat": 37.7785, "lon": -122.3893},
    "SEA": {"name": "T-Mobile Park",              "hr_factor": 1.02, "cf_bearing":   10, "lat": 47.5914, "lon": -122.3325},
    "STL": {"name": "Busch Stadium",              "hr_factor": 1.03, "cf_bearing":    0, "lat": 38.6226, "lon": -90.1929},
    "TB":  {"name": "Tropicana Field",            "hr_factor": 1.00, "cf_bearing":  340, "lat": 27.7683, "lon": -82.6534},
    "TEX": {"name": "Globe Life Field",           "hr_factor": 1.12, "cf_bearing":  350, "lat": 32.7473, "lon": -97.0827},
    "TOR": {"name": "Rogers Centre",              "hr_factor": 1.01, "cf_bearing":  350, "lat": 43.6414, "lon": -79.3892},
    "WSH": {"name": "Nationals Park",             "hr_factor": 1.04, "cf_bearing":  350, "lat": 38.8730, "lon": -77.0074},
}


def get_park(team_abbr: str) -> dict:
    return PARK_FACTORS.get(team_abbr.upper(), {
        "name": "Unknown Park", "hr_factor": 1.00, "lat": 39.5, "lon": -98.0
    })


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
