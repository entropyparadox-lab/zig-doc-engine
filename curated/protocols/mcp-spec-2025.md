# Model Context Protocol (MCP) Standard Specification

## 1. Architecture Overview
The Model Context Protocol (MCP) standardizes how AI applications and coding agents connect to local or remote data sources and tools.

- **Client**: The LLM agent runtime (e.g. Hermes, Claude Desktop, Cursor).
- **Server**: Exposes tools, resources, and prompts over standard transport layers.
- **Transports**:
  1. `stdio`: Standard input/output for local process isolation.
  2. `sse` / `http`: Server-Sent Events over HTTP for remote services.

## 2. Protocol Primitives (JSON-RPC 2.0)

### Initialization Handshake
```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": { "tools": {}, "resources": {} },
    "clientInfo": { "name": "hermes-agent", "version": "1.0.0" }
  }
}
```

### Tools Declaration & Schema (`tools/list`)
Servers advertise capabilities using standard JSON Schema:

```json
// Server -> Client
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "query_database",
        "description": "Execute a read-only SQL query against the application DB",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": { "type": "string", "description": "SQL SELECT query" },
            "limit": { "type": "integer", "default": 50 }
          },
          "required": ["query"]
        }
      }
    ]
  }
}
```

### Tool Execution (`tools/call`)
```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "query_database",
    "arguments": { "query": "SELECT * FROM users LIMIT 5" }
  }
}

// Server -> Client
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      { "type": "text", "text": "[{\"id\": 1, \"name\": \"Alice\"}]" }
    ],
    "isError": false
  }
}
```

## 3. Best Practices for MCP Implementations
1. **Idempotency & Safety**: Mark destructive tools explicitly in descriptions.
2. **Bounded Responses**: Avoid streaming megabytes of raw text into LLM context; truncate or paginate large lists.
3. **Structured Errors**: Return `isError: true` with clean diagnostic text rather than terminating the process.
