## 2026-01-30 - Pandas used for append-only logs
**Learning:** The codebase was using `pd.read_csv` + `pd.concat` + `df.to_csv` for appending a single row to a log file (`posted_history.csv`). This is O(N) and inefficient for growing logs.
**Action:** Replace such patterns with `csv` module's append mode (`'a'`) which is O(1) and memory efficient.
