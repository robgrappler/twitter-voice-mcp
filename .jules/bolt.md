## 2025-02-20 - Optimizing CSV Operations
**Learning:** Replacing `pandas` with `csv` module yielded ~60x speedup for simple append operations (0.003s vs 0.197s) and removed heavy dependency overhead for simple data persistence.
**Action:** Prefer standard library `csv` over `pandas` for simple row-based data logging/persistence in CLI/MCP tools where startup time matters.
