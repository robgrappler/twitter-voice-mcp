## 2025-05-15 - Path Traversal in MCP Tools
**Vulnerability:** MCP tools accepting file paths without validation allowing arbitrary file read.
**Learning:** MCP servers expose local filesystem access directly to LLMs/users. Inputs must be strictly sandboxed.
**Prevention:** Always validate file paths against a whitelist or safe directory using `os.path.commonpath` to ensure component-wise containment (avoiding `startswith` pitfalls).

## 2025-05-15 - CSV Injection in Exports
**Vulnerability:** User-generated content (tweets) starting with =, +, -, @ could execute formulas when exported to CSV and opened in Excel.
**Learning:** Raw data used by the application should be kept separate from user-facing exports. Sanitizing at storage level corrupts application data; sanitizing at export level is safer.
**Prevention:** Implement specific "Safe Export" functions that escape dangerous characters (prepends single quote) only for files intended for human consumption.

## 2025-05-15 - Prompt Injection via User Input
**Vulnerability:** Concatenating user input (topics, tweet text) directly into LLM prompts allows users to override system instructions (Persona/Ghostwriter).
**Learning:** Separating "System Instructions" (Voice Profile) from "User Data" (Topic) is critical. Using XML tags wraps user data, preventing it from being interpreted as commands.
**Prevention:** Use provider-specific 'system' instruction parameters/roles. Wrap untrusted user input in XML tags (e.g., `<topic>...</topic>`) within the user message.
