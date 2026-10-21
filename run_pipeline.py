import subprocess
import sys

# Scripts to run, in order
steps = [
    "etl/extract_mlb_api.py",   # extract: MLB Stats API schedule, 2022-2026
    "etl/check_bball_ref.py",   # extract: check the Baseball-Reference files 2022, 2023, 2024, 2025, and 2026
    "etl/check_savant.py",      # extract: check the Savant data 2022-2026
    "etl/transform.py",         # clean data, match keys and columns, align times, drop columns not needed,
                                # build features, build dimention tables, build ML table, handle missing values, and save CSVs
    "etl/load.py",              # rebuild tables, then load into Postgres
    "etl/quality_checks.py",    # print PASS/FAIL for each quality check
]

for step in steps:
    print(f"\n=== Running {step} ===")
    result = subprocess.run([sys.executable, step])

    if result.returncode != 0:
        print(f"\nStopped: {step} failed. Fix it and run again.")
        sys.exit(1)

print("\nPipeline finished.")