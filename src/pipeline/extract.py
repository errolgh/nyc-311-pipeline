import os
import argparse
from datetime import date, timedelta
import time
# from pathlib import Path
import requests as req
from dotenv import load_dotenv

load_dotenv()

# New York City 311 Service Requests dataset ID
dataset_id = "erm2-nwe9"
url = f"https://data.cityofnewyork.us/resource/{dataset_id}.json"

NYC_311_APP_TOKEN = os.getenv("NYC_311_APP_TOKEN")
if not NYC_311_APP_TOKEN: raise ValueError("NYC_311_APP_TOKEN environment variable is not set.")

headers = {"X-App-Token": NYC_311_APP_TOKEN}
lag_cutoff = date.today() - timedelta(days=3)

def extract_data(extraction_date):
    target_date_end = extraction_date + timedelta(days=1) if extraction_date else lag_cutoff + timedelta(days=1)

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
        json_data = response.json()

        offset_value += len(json_data)
        accumulated_list.extend(json_data)

        print(f"fetching {len(json_data)} items...\n total fetched items: {offset_value}\n")

        if len(json_data) < limit_value:
            break
        time.sleep(0.2)
        # Save accumulated data to a .jsonl file

# Runner and bash argument parser
def main():
    parser = argparse.ArgumentParser(description="Extract data from NYC 311 Service Requests dataset.")
    parser.add_argument("--date", default=lag_cutoff, type=date.fromisoformat, help="Date for which to extract data in YYYY-MM-DD format.")

    args = parser.parse_args()
    extract_data(extraction_date=args.date)

if __name__ == "__main__": main()
