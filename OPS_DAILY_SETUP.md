# MLB HR Engine — Daily Ops Scheduling Guide

## Confirmed paths

| Item | Path |
|------|------|
| Repo root | `C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master` |
| Python 3.12 | `C:\Users\ChrisPatrick\AppData\Local\Programs\Python\Python312\python.exe` |
| Bat launcher | `[repo]\run_ops_daily.bat` |
| Log file | `[repo]\logs\ops_daily_log.txt` |
| Daily reports | `[repo]\reports\daily_YYYY-MM-DD.txt` |

---

## What ops_daily.py does (6 phases)

Runs every morning. Targets **yesterday's** games by default.

| Phase | Action | Output |
|-------|--------|--------|
| 1 | Settle yesterday's picks via MLB Stats API | Updates `pick_tracker.csv` |
| 2 | Data integrity check (duplicates, stale, P&L accuracy) | Warns in log |
| 3 | Calibration drift monitor (9 dimensions, 3 alert levels) | Warns in log |
| 4 | CLV capture — fetch current odds, compute & store CLV | Updates `pick_tracker.csv` + `line_snapshots.csv` |
| 5 | CLV summary (avg pp, beats-close%, verdict) | Printed in log |
| 6 | ROI snapshot (win rate, ROI, net P&L) | Printed in log |

Report saved to: `reports/daily_YYYY-MM-DD.txt`. Old reports auto-deleted after 90 days.

---

## Step 1 — Register the Windows Task Scheduler task

Open **PowerShell as Administrator** and run:

```powershell
cd "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"
.\schedule_task.ps1
```

This registers a task named **"MLB HR Engine Daily Ops"** that runs `run_ops_daily.bat` at 8:00 AM every day.

- Safe to run multiple times — it checks for an existing task first and does nothing if already registered.
- Does **not** modify any model files, config, or CSV data.

---

## Step 2 — Verify the task is registered

```powershell
.\schedule_task.ps1 -Status
```

Expected output:
```
Task:         MLB HR Engine Daily Ops
State:        Ready
Last Run:     ...
Last Result:  0  (0 = success)
Next Run:     Tomorrow 8:00 AM
```

Or open Task Scheduler directly:

```
Win+R → taskschd.msc → Task Scheduler Library → "MLB HR Engine Daily Ops"
```

---

## Step 3 — Test the task manually (before relying on the schedule)

**Option A — Run the bat directly** (same as Task Scheduler will do):
```cmd
cd "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"
run_ops_daily.bat
```
Output appends to `logs\ops_daily_log.txt`.

**Option B — Run Python directly** (interactive, visible in terminal):
```powershell
cd "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"
py -3.12 -X utf8 ops_daily.py
```

**Option B with flags:**
```powershell
# Skip settlement (picks already settled for the day)
py -3.12 -X utf8 ops_daily.py --skip-settle

# Skip CLV capture (no active Odds API key or outside odds window)
py -3.12 -X utf8 ops_daily.py --skip-clv

# Run for a specific past date
py -3.12 -X utf8 ops_daily.py 2026-05-17

# Report only (no external API calls)
py -3.12 -X utf8 ops_daily.py --report-only
```

---

## Daily operational workflow

| Time | Action | Command |
|------|--------|---------|
| 8:00 AM | Auto: settle + integrity + drift + CLV + ROI | Task Scheduler (automatic) |
| ~30 min before first pitch | Manual: capture closing lines for CLV | `py -3.12 capture_closing_lines.py` |
| After picks are generated | Manual: run portfolio optimizer | `py -3.12 optimize_daily.py` |
| Weekly | Manual: full health dashboard | `py -3.12 monitoring_dashboard.py` |

> **Note:** `capture_closing_lines.py` must be run manually ~30 min before first pitch — it cannot be scheduled at a fixed time because game start times vary. A separate Task Scheduler entry at a fixed time (e.g., 6:30 PM ET) could automate this if games reliably start after that.

---

## Inspecting logs and reports

### Live log tail (PowerShell)
```powershell
Get-Content "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master\logs\ops_daily_log.txt" -Tail 60
```

### Today's report
```powershell
$today = (Get-Date).ToString("yyyy-MM-dd")
Get-Content "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master\reports\daily_$today.txt"
```

### List all reports
```powershell
Get-ChildItem "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master\reports" -Filter "daily_*.txt" | Sort-Object Name -Descending
```

### Full monitoring dashboard
```powershell
cd "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"
py -3.12 monitoring_dashboard.py
```
Output: `monitoring_dashboard_output.txt`

---

## Removing the scheduled task

```powershell
.\schedule_task.ps1 -Remove
```

Or via Task Scheduler UI: right-click task → Delete.

---

## Troubleshooting

### Task runs but log is empty or shows Python error
Check the log:
```powershell
Get-Content logs\ops_daily_log.txt -Tail 50
```
Common causes:
- `ODDS_API_KEY` not set in `.env` inside `mlb_hr_engine_v4/` → Phase 4 will skip CLV automatically (not an error)
- No picks in `pick_tracker.csv` for yesterday → settlement shows 0 new picks (normal early in season)
- MLB Stats API timeout → Phase 1 logs `[FAILED]` with exception; retry with `--skip-settle` if it persists

### Task doesn't run at 8 AM
- Confirm machine is powered on and not sleeping at 8 AM (Settings → Power → Sleep)
- In Task Scheduler, check "History" tab for the task to see last run result
- The task runs only when the user is logged on (`Interactive` logon type). If you need it to run when locked/logged off, re-register with `RunLevel = HighestAvailable` and supply password — contact IT for group policy implications.

### "Access denied" when registering
Re-run `schedule_task.ps1` from an **elevated** PowerShell (right-click → Run as Administrator).

### OneDrive sync conflict on CSV files
If OneDrive is syncing `pick_tracker.csv` or `line_snapshots.csv` during a write, you may see transient lock errors. The tracking modules use atomic writes (`temp file + os.replace`) which minimize this window. If conflicts persist, consider pausing OneDrive sync during the 8 AM ops window.

---

## Model-freeze reminder

The following must NOT be changed via ops scripts or Task Scheduler automation:
- Model formulas, thresholds, calibration logic, optimizer thresholds
- Arsenal signals, pitcher factor scale, EV/edge thresholds
- Any file in `mlb_hr_engine_v4/engine/` or `mlb_hr_engine_v4/clients/`

`ops_daily.py`, `capture_closing_lines.py`, and `optimize_daily.py` are read-only with respect to the model — they only write to CSV tracking files and text reports.
