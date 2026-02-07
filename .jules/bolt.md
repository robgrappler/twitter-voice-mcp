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
**Learning:** Reading the voice profile from disk (`voice_profile.txt`) on every generation request was redundant and added unnecessary I/O overhead.
**Action:** Implemented in-memory caching in `AIHandler` using `_voice_profile_cache` and consolidated write operations into `save_voice_profile` to ensure cache consistency, resulting in a ~573x speedup for profile access.
