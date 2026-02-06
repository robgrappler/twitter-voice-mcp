## 2025-05-15 - Path Traversal in MCP Tools

**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports

**Vulnerability:** CSV Formula Injection (Excel formulas starting with =, +, -, or @) in user-generated content could execute malicious code when exported CSV files are opened in spreadsheets.
**Learning:** Sanitizing inputs at the storage level can break application functionality if the data is used internally (e.g., as a database). Sanitizing only during export for user consumption is safer and maintains data integrity.
**Prevention:** Implement dedicated "Safe Export" methods that prepend a single quote to escape dangerous characters only for files intended for human consumption, keeping internal storage raw.

## 2025-05-15 - Prompt Injection in AI Handlers
**Vulnerability:** Direct concatenation of user input into LLM system prompts allowed "Indirect Prompt Injection" where user content could override system instructions.
**Learning:** Quoting user input is insufficient defense against modern LLMs. XML tagging provides a stronger boundary that models can be instructed to respect.
**Prevention:** Wrap all user-provided content in distinct XML tags (e.g., `<topic>`) and explicitly instruct the model in the system prompt to treat content within those tags strictly as data, not instructions.
