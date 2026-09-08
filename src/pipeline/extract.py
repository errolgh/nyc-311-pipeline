import argparse
from datetime import date, timedelta
from dotenv import load_dotenv
import json
import os
from pathlib import Path
import random
import requests as req
import time

load_dotenv()

# Both the file write and idempotent reruns are one design, not two:
# - Deterministic path: the date fully determines where output goes: `data/raw/311/date=2026-08-09/requests.jsonl`
# - Format: one JSON object per line (jsonl)
# - Atomic overwrite: 
#   write to `requests.jsonl.tmp` in the same directory, then replace if successful.
#   Rerunning a date replaces its partition wholesale. No appends, no dedup logic, no half-written files if the process dies mid-run.
# - Extract this as `write_partition(records, date) -> Path`.

# New York City 311 Service Requests

DATASET_ID = "erm2-nwe9"

def load_config():
    token = os.getenv("NYC_311_APP_TOKEN")
    if not token:
        raise ValueError("NYC_311_APP_TOKEN environment variable is not set.")
    return {
        "order": "created_date ASC, unique_key ASC",
        "url": f"https://data.cityofnewyork.us/resource/{DATASET_ID}.json",
        "headers": {"X-App-Token": token}
    }

def build_params(extraction_date, order, offset, limit, select=None):
    date_end = extraction_date + timedelta(days=1)
    params = {
        '$where': f"created_date >= '{extraction_date}T00:00:00' AND created_date < '{date_end}T00:00:00'",
        "$order": order,
        "$offset": offset,
        "$limit": limit
    }
    if select:
        params['$select'] = select
    return params

def fetch_all_records(extraction_date, config):
    accumulated_list = []
    offset_value = 0
    limit_value = 1000

    while True: 
        params = build_params(extraction_date, config["order"], offset_value, limit_value)

        json_data = fetch_page(config["url"], params, config["headers"])

        offset_value += len(json_data)
        accumulated_list.extend(json_data)
    
        print(f"fetching {len(json_data)} items...\n total fetched items: {offset_value}\n")
    
        if len(json_data) < limit_value:
            break
        time.sleep(0.2)
    return accumulated_list

def fetch_page(url, params, headers):
    retries = 5

    for attempt in range(retries):
        remaining_attempts = retries-attempt
        try:
            response = req.get(url, params=params, headers=headers, timeout=60)

            if response.status_code == 429 or response.status_code >= 500:
                raise req.HTTPError(f"Status {response.status_code}")

            response.raise_for_status()  # Error response would otherwise still write a file with error payload
            json_data = response.json()
            return json_data

        except req.Timeout:
            print(f"Timeout error. Retries remaining: {remaining_attempts}.")

        except req.ConnectionError:
            print(f"Connection error. Retries remaining: {remaining_attempts}")

        except req.HTTPError as e:
            if e.response is not None:
                code = e.response.status_code
                if 400 <= code < 500 and code !=429:
                    raise
            print(f"HTTP error: {e}. Retries remaining: {remaining_attempts}.")

        if attempt < retries - 1:
            backoff = 2**attempt
            time.sleep(backoff + random.uniform(0, 1))

    raise RuntimeError(f"Closing resources. Unable to retrieve records after {retries} times.")

def fetch_record_count(extraction_date, config):
    params = build_params(extraction_date, None, 0, 1, "count(*)")
    count = int(fetch_page(config["url"], params, config["headers"])[0]["count"])
    return count

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

def extract_data(extraction_date, lag_cutoff, config):
    target_date_end = extraction_date + timedelta(days=1)
    count = fetch_record_count(extraction_date, config)

    print(f"Extracting {count} records from {extraction_date} to {target_date_end}...")

    if extraction_date > lag_cutoff:
        print(f"Warning: {extraction_date} is within the 3-day publication lag. Data may be incomplete.")
    records = fetch_all_records(extraction_date, config)

    if len(records) != count:
        raise ValueError(f"Expected {count} records, got {len(records)}.")

    save_to_jsonl(records, extraction_date)

# Runner and bash argument parser
def main():
    config = load_config()
    lag_cutoff = date.today() - timedelta(days=3)

    parser = argparse.ArgumentParser(description="Extract data from NYC 311 Service Requests dataset.")
    parser.add_argument("--date", default=lag_cutoff, type=date.fromisoformat, help="Date for which to extract data in YYYY-MM-DD format.")

    args = parser.parse_args()
    extract_data(extraction_date=args.date, lag_cutoff=lag_cutoff, config=config)

if __name__ == "__main__": main()
