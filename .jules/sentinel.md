## 2025-05-15 - Path Traversal in MCP Tools

**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports

**Vulnerability:** CSV Formula Injection (Excel formulas starting with =, +, -, or @) in user-generated content could execute malicious code when exported CSV files are opened in spreadsheets.
**Learning:** Sanitizing inputs at the storage level can break application functionality if the data is used internally (e.g., as a database). Sanitizing only during export for user consumption is safer and maintains data integrity.
**Prevention:** Implement dedicated "Safe Export" methods that prepend a single quote to escape dangerous characters only for files intended for human consumption, keeping internal storage raw.

## 2025-01-27 - Prompt Injection in AI Handlers
**Vulnerability:** User input (e.g., `topic`) was directly interpolated into the LLM prompt without sanitization.
**Learning:** LLMs can be tricked into ignoring previous instructions if user input contains specific phrases or structural delimiters (like quotes) that break the intended prompt format.
**Prevention:** Always sanitize user input (e.g., `html.escape`) and wrap it in XML tags (e.g., `<topic>...</topic>`) within the prompt, explicitly instructing the model to treat the tagged content as data.
