## 2025-01-27 - [Pandas vs CSV Append]
**Learning:** Appending to a CSV file using `pandas.read_csv` + `pd.concat` + `to_csv` is O(N) and inefficient for growing log files.
**Action:** Use Python's built-in `csv` module with append mode (`'a'`) for O(1) logging operations, ensuring column order matches the schema.
