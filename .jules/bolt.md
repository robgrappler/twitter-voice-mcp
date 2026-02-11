## 2025-01-27 - [Pandas vs CSV Append]
**Learning:** Appending to a CSV file using `pandas.read_csv` + `pd.concat` + `to_csv` is O(N) and inefficient for growing log files.
**Action:** Use Python's built-in `csv` module with append mode (`'a'`) for O(1) logging operations, ensuring column order matches the schema.

## 2025-01-27 - [Twitter API Caching]
**Learning:** Repeated lookups of the same username via Twitter API (e.g., during voice analysis) are redundant and slow.
**Action:** Implement a simple in-memory cache (dict) for username->ID lookups and cache the authenticated user's ID to reduce API latency and cost.

## 2025-01-27 - [Lazy Loading AI Libraries]
**Learning:** Top-level imports of heavy AI client libraries (google.generativeai, openai, anthropic) caused a ~2.7s startup delay.
**Action:** Implemented lazy loading by moving imports inside `configure` and `_call_model` methods, reducing import time to ~0.1s and only loading what is needed.

## 2025-01-27 - [Voice Profile Caching]
**Learning:** The voice profile file (`voice_profile.txt`) was being read from disk on every tweet generation request, adding unnecessary I/O overhead.
**Action:** Implemented an in-memory cache in `AIHandler` that stores the profile after the first read or analysis, and updates it on save, reducing file reads to once per session (or update).

## 2025-01-27 - [Removing Pandas Dependency in DataHandler]
**Learning:** Importing `pandas` adds ~0.5s to startup time and loading entire CSVs into DataFrames for single-row updates consumes unnecessary memory (O(N) load vs O(1) buffer).
**Action:** Replaced all `pandas` usage in `src/data_handler.py` with the standard `csv` module (streaming read/write), reducing memory usage by ~14x for large files and eliminating the heavy import cost for the module.
