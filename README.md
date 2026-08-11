A production-style batch ELT pipeline over New York City's 311 service request data, built to handle the problems real pipelines have: records that update after they're loaded, reruns that have to be safe, and backfills across months of history.

Roughly 8,000 service requests are filed daily and many change status days later, which makes this a realistic stand-in for high-volume event data with late-arriving updates.

Code is MIT licensed. The 311 data itself belongs to NYC Open Data and is subject to their terms of use.
