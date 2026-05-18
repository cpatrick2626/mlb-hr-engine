@echo off
:: MLB HR Engine — Daily Operations Runner
:: Schedule via Windows Task Scheduler to run at 8:00 AM daily.
:: Settles yesterday's picks, checks data integrity, monitors calibration drift,
:: and generates a daily report in the reports/ directory.

cd /D "C:\Users\ChrisPatrick\OneDrive - Resilience\Desktop\MLB HR Engine\mlb-hr-engine-master"

py -3.12 -X utf8 ops_daily.py >> logs\ops_daily_log.txt 2>&1
