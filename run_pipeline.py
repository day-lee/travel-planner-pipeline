"""
Build the DuckDB warehouse from the raw files. 
Add --fetch to call the APIs first.
"""

import os
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "travel_planner_warehouse.duckdb"
INGESTION_SCRIPTS = ("ingest/api_uk_holidays.py", "ingest/api_weather.py")

os.chdir(ROOT) 

if "--fetch" in sys.argv:
    for script in INGESTION_SCRIPTS:
        subprocess.run([sys.executable, script], check=True)
    
DB_PATH.unlink(missing_ok=True) 

with duckdb.connect(str(DB_PATH)) as con:
    for sql_file in sorted(Path("sql").rglob("*.sql")): 
        print(f"Running: {sql_file}")
        con.execute(sql_file.read_text(encoding="utf-8"))

print(f"Done. Warehouse: {DB_PATH.name}")