## 2025-01-27 - [Pandas vs CSV Append]
**Learning:** Appending to a CSV file using `pandas.read_csv` + `pd.concat` + `to_csv` is O(N) and inefficient for growing log files.
**Action:** Use Python's built-in `csv` module with append mode (`'a'`) for O(1) logging operations, ensuring column order matches the schema.

## 2025-01-27 - [API ID Caching]
**Learning:** External APIs often require ID-based lookups. Fetching these IDs repeatedly for the same entity (e.g., username) wastes rate limits and adds latency.
**Action:** Implement a simple in-memory cache (dictionary) for ID lookups within the API handler class to prevent redundant network calls.
