import os
import json
import argparse
from datetime import date, timedelta
import time
from pathlib import Path
import requests as req
from dotenv import load_dotenv
load_dotenv()

# TODO: Refactor into smaller functions for better testing and maintainability.

# New York City 311 Service Requests dataset ID
dataset_id = "erm2-nwe9"
url = f"https://data.cityofnewyork.us/resource/{dataset_id}.json"

NYC_311_APP_TOKEN = os.getenv("NYC_311_APP_TOKEN")
if not NYC_311_APP_TOKEN: raise ValueError("NYC_311_APP_TOKEN environment variable is not set.")

headers = {"X-App-Token": NYC_311_APP_TOKEN}

# Both the file write and idempotent reruns are one design, not two:
# - Deterministic path: the date fully determines where output goes: `data/raw/311/date=2026-08-09/requests.jsonl`
# - Format: one JSON object per line (jsonl)
# - Atomic overwrite: 
#   write to `requests.jsonl.tmp` in the same directory, then replace if successful.
#   Rerunning a date replaces its partition wholesale. No appends, no dedup logic, no half-written files if the process dies mid-run.
# - Extract this as `write_partition(records, date) -> Path`.

def save_to_jsonl(data, extraction_date):
    output_dir = Path(f"data/raw/311/date={extraction_date}")
    output_dir.mkdir(parents=True, exist_ok=True)
    final_output_file = output_dir / "requests.jsonl" #append file extension
    temp_file = output_dir / "requests.jsonl.tmp" #temp file for atomic write

    with temp_file.open("w", encoding="utf-8") as f:
        for record in data:
            f.write(f"{json.dumps(record)}\n")

    os.replace(temp_file, final_output_file)
    return final_output_file #for caller

def extract_data(extraction_date, lag_cutoff):
    target_date_end = extraction_date + timedelta(days=1)

    print(f"Extracting {extraction_date} to {target_date_end}...")

    if extraction_date > lag_cutoff:
        print(f"Warning: {extraction_date} is within the 3-day publication lag. Data may be incomplete.")

    accumulated_list = []
    offset_value = 0
    limit_value = 1000

    while True:
        params = {
            "$where": f"created_date >= '{extraction_date}T00:00:00' AND created_date < '{target_date_end}T00:00:00'",
            "$order": "created_date ASC, unique_key ASC",
            "$offset": offset_value,
            "$limit": limit_value,
        }


        response = req.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()  # Error response would otherwise still write a file with error payload
        json_data = response.json()

        offset_value += len(json_data)
        accumulated_list.extend(json_data)

        print(f"fetching {len(json_data)} items...\n total fetched items: {offset_value}\n")

        if len(json_data) < limit_value:
            break
        time.sleep(0.2)

    # Save accumulated data to a .jsonl file
    save_to_jsonl(accumulated_list, extraction_date)

# Runner and bash argument parser
def main():
    load_config()

    lag_cutoff = date.today() - timedelta(days=3)

    parser = argparse.ArgumentParser(description="Extract data from NYC 311 Service Requests dataset.")
    parser.add_argument("--date", default=lag_cutoff, type=date.fromisoformat, help="Date for which to extract data in YYYY-MM-DD format.")

    args = parser.parse_args()
    extract_data(extraction_date=args.date, lag_cutoff=lag_cutoff)

if __name__ == "__main__": main()
