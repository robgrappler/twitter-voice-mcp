## 2025-05-15 - Path Traversal in MCP Tools

**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports

**Vulnerability:** CSV Formula Injection (Excel formulas starting with =, +, -, or @) in user-generated content could execute malicious code when exported CSV files are opened in spreadsheets.
**Learning:** Sanitizing inputs at the storage level can break application functionality if the data is used internally (e.g., as a database). Sanitizing only during export for user consumption is safer and maintains data integrity.
**Prevention:** Implement dedicated "Safe Export" methods that prepend a single quote to escape dangerous characters only for files intended for human consumption, keeping internal storage raw.

## 2025-05-15 - Prompt Injection in AI Tools
**Vulnerability:** User inputs (e.g., topics, tweet text) were directly interpolated into LLM prompts via f-strings, allowing attackers to override instructions.
**Learning:** LLMs treat all input as instructions unless explicitly structured otherwise. Simple string formatting is insufficient for security.
**Prevention:** Wrap user inputs in XML tags (e.g. `<topic>...</topic>`), HTML-escape the content to prevent tag spoofing, and explicitly instruct the model to treat the wrapped content as data/context.
