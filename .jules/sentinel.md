## 2025-05-15 - Path Traversal in MCP Tools
**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports
**Vulnerability:** CSV Formula Injection allows executing code via malicious formulas in exported CSV files.
**Learning:** Sanitizing inputs on write can break application functionality if the CSV is also used as an internal database.
**Prevention:** Sanitize data only when exporting for user consumption (e.g., via a dedicated export method), keeping the internal storage raw/functional.
