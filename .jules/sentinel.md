## 2025-05-15 - Path Traversal in MCP Tools
**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports
**Vulnerability:** User-generated content (tweets) starting with =, +, -, @ could execute formulas when exported to CSV and opened in Excel.
**Learning:** Raw data used by the application should be kept separate from user-facing exports. Sanitizing at storage level corrupts application data; sanitizing at export level is safer.
**Prevention:** Implement specific "Safe Export" functions that escape dangerous characters (prepends single quote) only for files intended for human consumption.

## 2025-05-15 - Prompt Injection via LLM API Concatenation
**Vulnerability:** User input was concatenated directly into the prompt string alongside system instructions, allowing users to override constraints.
**Learning:** LLM APIs (Gemini, OpenAI, Anthropic) provide specific mechanisms (system_instruction, system role) to separate instructions from data. Concatenation is insecure.
**Prevention:** Always use the provider's native system prompt separation feature. Refactor code to accept system instructions separately from user prompts.
