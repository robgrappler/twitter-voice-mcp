## 2025-05-15 - Path Traversal in MCP Tools

**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports

**Vulnerability:** CSV Formula Injection (Excel formulas starting with =, +, -, or @) in user-generated content could execute malicious code when exported CSV files are opened in spreadsheets.
**Learning:** Sanitizing inputs at the storage level can break application functionality if the data is used internally (e.g., as a database). Sanitizing only during export for user consumption is safer and maintains data integrity.
**Prevention:** Implement dedicated "Safe Export" methods that prepend a single quote to escape dangerous characters only for files intended for human consumption, keeping internal storage raw.

## 2025-05-15 - Prompt Injection in AI Handlers

**Vulnerability:** User-controlled inputs interpolated directly into LLM prompts without sanitization or structural boundaries, allowing prompt injection.
**Learning:** LLMs can be tricked into executing malicious instructions if user input is not clearly distinguished from system instructions.
**Prevention:** Sanitize user inputs (e.g., escape XML tags) and wrap them in structured delimiters (like <input>...</input>). Explicitly instruct the model to treat the content within these tags as data, not instructions.
