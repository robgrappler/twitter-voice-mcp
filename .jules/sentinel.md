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

## 2025-05-15 - Prompt Injection in AI Handlers (Correction)

**Vulnerability:** User-controlled inputs (tweets, topics) were injected directly into LLM prompts.
**Learning:** html.escape can be too aggressive for style analysis where character fidelity matters (e.g., quotes). A balanced approach is needed.
**Prevention:**
1. For data analysis (analyze_style): Use JSON serialization wrapped in XML tags (<tweets>) to safely encapsulate content without escaping characters.
2. For generation (generate_tweet): Use html.escape(..., quote=False) to prevent tag injection (< and >) while preserving quotes for natural language output.
