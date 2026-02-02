## 2025-05-15 - Path Traversal in MCP Tools
**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports
**Vulnerability:** User-generated content (tweets) starting with =, +, -, @ could execute formulas when exported to CSV and opened in Excel.
**Learning:** Raw data used by the application should be kept separate from user-facing exports. Sanitizing at storage level corrupts application data; sanitizing at export level is safer.
**Prevention:** Implement specific "Safe Export" functions that escape dangerous characters (prepends single quote) only for files intended for human consumption.

## 2025-05-15 - Prompt Injection via Unified Prompts
**Vulnerability:** Constructing prompts by concatenating system instructions and user input into a single string allows malicious user input to override system instructions.
**Learning:** Modern LLM APIs (Gemini, OpenAI, Anthropic) provide dedicated fields for System Instructions. Using these ensures the model treats instructions as authoritative and user input as data/content.
**Prevention:** Always separate `system_instruction` (persona, constraints) from `user_prompt` (task, data) in code, and pass them to the API using the provider's specific mechanism (e.g., `system_instruction` arg, `system` role).
