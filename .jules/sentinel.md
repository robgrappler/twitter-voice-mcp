## 2025-05-15 - Path Traversal in MCP Tools

**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports

**Vulnerability:** CSV Formula Injection (Excel formulas starting with =, +, -, or @) in user-generated content could execute malicious code when exported CSV files are opened in spreadsheets.
**Learning:** Sanitizing inputs at the storage level can break application functionality if the data is used internally (e.g., as a database). Sanitizing only during export for user consumption is safer and maintains data integrity.
**Prevention:** Implement dedicated "Safe Export" methods that prepend a single quote to escape dangerous characters only for files intended for human consumption, keeping internal storage raw.

## 2025-05-15 - Prompt Injection in AI Handlers

**Vulnerability:** User-controlled inputs (tweets, topics) were injected directly into LLM prompts, allowing malicious payloads to override system instructions.
**Learning:** LLMs are susceptible to prompt injection if data and instructions are mixed without clear delineation. JSON serialization alone is insufficient if the model interprets the content as instructions.
**Prevention:** Sanitize inputs using HTML escaping (`html.escape`) and wrap them in XML tags (e.g., `<tweets>...</tweets>`) to structurally separate data from instructions.

## 2025-05-15 - Symlink Path Traversal

**Vulnerability:** Path validation using `os.path.abspath` allowed traversal outside the safe directory via symbolic links (Time-of-Check Time-of-Use or static symlink traversal).
**Learning:** `os.path.abspath` only resolves `.` and `..` but does not resolve symbolic links. Validating a path that contains symlinks against a safe directory check can be bypassed if the symlink points outside.
**Prevention:** Use `os.path.realpath` to resolve the canonical path (including all symlinks) before validating it against the allowed directory. Also ensure the safe directory path itself is resolved with `realpath`.
