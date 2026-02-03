## 2025-05-15 - Path Traversal in MCP Tools
**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports
**Vulnerability:** User-generated content (tweets) starting with =, +, -, @ could execute formulas when exported to CSV and opened in Excel.
**Learning:** Raw data used by the application should be kept separate from user-facing exports. Sanitizing at storage level corrupts application data; sanitizing at export level is safer.
**Prevention:** Implement specific "Safe Export" functions that escape dangerous characters (prepends single quote) only for files intended for human consumption.

## 2025-05-15 - Indirect Prompt Injection in AI Handler
**Vulnerability:** User inputs (topics, search results) were concatenated directly into the prompt, allowing potential instruction override.
**Learning:** LLMs can be tricked by "Indirect Prompt Injection" where untrusted data contains instructions.
**Prevention:** Separate system instructions (voice profile) from user data using API-specific `system` parameters (OpenAI/Anthropic/Gemini) and delimit untrusted data with XML tags (e.g. `<topic>`).
