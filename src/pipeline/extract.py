# coding: utf-8

# python -m pipeline.extract --date 2026-08-09

# Requirements:

# Takes a --date argument. Everything downstream depends on this.
# Pages until it runs out, using $limit and $offset.
# Filters on created_date in SoQL. Use the shape we drilled: >= the day and < the next day. Not BETWEEN. That upper bound being exclusive is what keeps midnight records from landing in two files.
# Writes newline-delimited JSON: one complete record per line, no wrapping array, no commas between. It's the format warehouses load natively and the one you can append to and split. Get used to the extension .jsonl.
# Writes to a path with the date in it, like data/raw/311/date=2026-08-09/requests.jsonl. That key=value folder naming is the standard partitioning convention and it carries over unchanged when this becomes an S3 key.
# Overwrites that file on rerun rather than appending.

# One thing to think through before you write the loop:
# offset pagination assumes the underlying data holds still while you page through it.
# New 311 requests are being filed the entire time you're running.
# What could you add to your query to make the ordering deterministic so page 3 doesn't repeat or skip rows from page 2?
# The answer is one parameter, and knowing why you added it is a good interview beat.

import os
import pipeline as pl


socrata_domain = "opendata.socrata.com"
socrata_dataset_identifier = "f92i-ik66"

socrata_token = os.environ.get("NYC_311_APP_TOKEN")

