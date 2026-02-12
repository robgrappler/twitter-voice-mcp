## 2025-05-15 - Path Traversal in MCP Tools

**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports

**Vulnerability:** CSV Formula Injection (Excel formulas starting with =, +, -, or @) in user-generated content could execute malicious code when exported CSV files are opened in spreadsheets.
**Learning:** Sanitizing inputs at the storage level can break application functionality if the data is used internally (e.g., as a database). Sanitizing only during export for user consumption is safer and maintains data integrity.
**Prevention:** Implement dedicated "Safe Export" methods that prepend a single quote to escape dangerous characters only for files intended for human consumption, keeping internal storage raw.

## 2025-05-15 - Prompt Injection in AI Handler

**Vulnerability:** User inputs (`voice_profile`, `topic`, `tweets`) were directly interpolated into LLM prompts using XML-like structure tags (`<voice_profile>`), allowing attackers to break out of the structure and inject instructions.
**Learning:** LLMs are susceptible to prompt injection when structured data is mixed with instructions without proper boundaries or sanitization. Even internal data like `voice_profile` can be a vector if it originates from untrusted sources (e.g., analyzed tweets).
**Prevention:** Sanitize all variable inputs using `html.escape()` before injecting them into prompts, especially when using XML/HTML tags as delimiters. This ensures structure tags are preserved while content is treated as text.
