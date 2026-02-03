## 2025-01-27 - [Pandas vs CSV Append]
**Learning:** Appending to a CSV file using `pandas.read_csv` + `pd.concat` + `to_csv` is O(N) and inefficient for growing log files.
**Action:** Use Python's built-in `csv` module with append mode (`'a'`) for O(1) logging operations, ensuring column order matches the schema.

## 2025-01-27 - [Twitter API Caching]
**Learning:** Repeated lookups of the same username via Twitter API (e.g., during voice analysis) are redundant and slow.
**Action:** Implement a simple in-memory cache (dict) for username->ID lookups and cache the authenticated user's ID to reduce API latency and cost.
