@echo off
:: MLB HR Engine — Closing Line Capture
:: Schedule via Windows Task Scheduler ~30 min before first pitch (~6:45 PM ET).
:: Fetches current HR odds, computes CLV, writes closing columns to clv_log.csv.

cd /D "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"

py -3.12 -X utf8 mlb_hr_engine_v4\scripts\ops\capture_closing_lines.py >> logs\capture_closing_lines_log.txt 2>&1
