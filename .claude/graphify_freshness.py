import os, subprocess, sys

GRAPH = "mlb_hr_engine_v4/graphify-out/graph.json"

if not os.path.exists(GRAPH):
    sys.exit(0)  # missing — hook stays silent

graph_mtime = os.path.getmtime(GRAPH)

try:
    r = subprocess.run(
        ["git", "log", "--format=%ct", "--max-count=1", "--",
         "mlb_hr_engine_v4/", ":(exclude)mlb_hr_engine_v4/graphify-out/"],
        capture_output=True, text=True, timeout=5
    )
    commit_time = int(r.stdout.strip()) if r.stdout.strip() else 0
except Exception:
    commit_time = 0

print("STALE" if commit_time > graph_mtime else "FRESH")
