# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for JoeAPI, a construction management system. It exposes REST API endpoints as MCP tools, making construction management data accessible to AI assistants like Claude.

The repository contains **two implementations**:

### 1. TypeScript Implementation (Legacy)
- **Files**: `index.ts`, `local-server.ts`
- **Transports**: Smithery HTTP, STDIO
- **Framework**: `@modelcontextprotocol/sdk`
- **Status**: Original implementation, fully functional

### 2. Python/FastMCP Implementation (Recommended)
- **File**: `joeapi_server.py`
- **Transports**: HTTP (FastMCP Cloud), STDIO (local)
- **Framework**: FastMCP (Python)
- **Status**: New implementation for FastMCP Cloud deployment
- **Benefits**: Simpler syntax, built-in auth, free cloud hosting

## Build and Development Commands

### Smithery HTTP Mode (Default)
```bash
npm run dev          # Opens Smithery interactive playground
npm run build        # Alias for build:http
npm run build:http   # Build for Smithery deployment
npm run start        # Alias for start:http
npm run start:http   # Run Smithery HTTP server
```

### STDIO Mode (Local Claude Desktop)
```bash
npm run dev:stdio    # Development with tsx (TypeScript execution)
npm run build:stdio  # Compile TypeScript to ./build/
npm run start:stdio  # Run compiled STDIO server
```

## Architecture

### Core Files
- `index.ts` - Main MCP server implementation (1013 lines)
  - Exports `createServer()` function for Smithery
  - Exports `configSchema` with Zod validation
  - Contains `main()` function for STDIO transport
  - Defines 26+ tools using `server.registerTool()`
- `local-server.ts` - Minimal STDIO wrapper that imports and runs index.ts
- `build/` - Compiled JavaScript output (STDIO mode)
- `.smithery/` - Smithery build artifacts (HTTP mode)

### Dual Transport Architecture

The server uses a **unified codebase** that supports both transports:

**Smithery Export Pattern:**
```typescript
export const configSchema = z.object({
  apiBaseUrl: z.string().url().default('https://joeapi.fly.dev'),
  requestTimeout: z.number().optional().default(30000),
  apiKey: z.string().optional(),
});

export default function createServer({ config }) {
  const server = new McpServer({ name: 'joe-api-server', version: '1.0.0' });
  // ... register tools ...
  return server.server;
}
```

**STDIO Main Function:**
```typescript
async function main() {
  const apiBaseUrl = process.env.JOEAPI_BASE_URL || 'https://joeapi.fly.dev';
  const server = createServer({ config: { apiBaseUrl } });
  const transport = new StdioServerTransport();
  await server.connect(transport);
}
```

### Tool Registration Pattern

All tools use the **new McpServer API** with `server.registerTool()`:

```typescript
server.registerTool(
  'tool_name',                    // Tool identifier
  {
    title: 'Human Readable Title',
    description: 'What this tool does',
    inputSchema: {                // Zod schema
      param: z.string().describe('Parameter description'),
    },
  },
  async ({ param }) => {          // Handler function
    return makeRequest('GET', '/endpoint', null, { param });
  }
);
```

**Key difference from old pattern:** No manual `ListToolsRequestSchema` or `CallToolRequestSchema` handlers - the new API handles this automatically.

### Tool Categories

**26+ tools across 7 categories:**

1. **Clients & Contacts** - `list_clients`, `create_client`, `list_contacts`, `create_contact`
2. **Proposals** - `list_proposals`, `create_proposal`, `find_proposal`
3. **Estimates** - Estimate management tools
4. **Projects** - `find_project`, `get_project_details`, `list_schedules`
5. **Action Items** - `find_action_items`, task tracking
6. **Financial** - `get_financials`, `get_transactions` (with parallel data fetching)
7. **Search** - `search` (generic multi-type search), `find_proposal`, `find_action_items`

### Special Tools

#### `async` tool (index.ts:552-728)
Delegates complex workflows to external async-agent service:
- **Endpoint:** `https://joeapi-async-agent.fly.dev/webhooks/prompt-stream`
- **Transport:** Server-Sent Events (SSE) streaming
- **Timeout:** 6 minutes (360,000ms)
- **Features:**
  - Real-time progress updates via SSE
  - Synchronous mode (`async: false` in payload)
  - Detailed console logging for debugging
  - Graceful timeout handling with AbortController

**SSE Processing Pattern:**
```typescript
// Stream reading with buffer management
const reader = response.body?.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split('\n\n');
  buffer = lines.pop() || '';

  for (const line of lines) {
    if (!line.startsWith('data: ')) continue;
    const eventData = JSON.parse(line.substring(6));

    if (eventData.type === 'complete') {
      finalResult = eventData.data;
    } else if (eventData.type === 'progress') {
      console.error(`Progress: ${eventData.message}`);
    }
  }
}
```

#### `get_financials` tool (index.ts:734-768)
Demonstrates parallel API fetching pattern:
```typescript
const [jobBalancesResult, costVarianceResult] = await Promise.all([
  makeRequest('GET', '/job-balances', null, { projectId }),
  makeRequest('GET', '/cost-variance', null, { projectId })
]);
```

### Configuration

**Environment Variables:**
- `JOEAPI_BASE_URL` - Base URL for JoeAPI (defaults to `https://joeapi.fly.dev`)
  - For local development: `http://localhost:8080`
  - Configure in Claude Desktop config or shell environment
- `JOEAPI_API_KEY` - Optional API key for authentication

**Smithery Config (via dashboard):**
- `apiBaseUrl` - Base URL for JoeAPI
- `requestTimeout` - Request timeout in milliseconds (default: 30000)
- `apiKey` - Optional API key

**TypeScript Configuration:**
- Target: ES2022
- Module: Node16 with ESM
- Strict mode enabled
- Output directory: `./build`
- Excludes: `node_modules`, `build`, `index-migrated.ts`, `index.ts.backup`

## Adding New Tools

1. **Add tool registration** in `index.ts` within the appropriate category section:
```typescript
server.registerTool(
  'my_new_tool',
  {
    title: 'My New Tool',
    description: 'Clear description of what this tool does',
    inputSchema: {
      paramName: z.string().describe('Parameter description'),
      optionalParam: z.number().optional().describe('Optional parameter'),
    },
  },
  async ({ paramName, optionalParam }) => {
    return makeRequest('GET', '/api-endpoint', null, {
      paramName,
      ...(optionalParam && { optionalParam }),
    });
  }
);
```

2. **Rebuild:**
   - Smithery: `npm run build` (automatic deployment)
   - STDIO: `npm run build:stdio` then restart Claude Desktop

## Common Patterns

### Simple GET with query params
```typescript
server.registerTool('list_items', { ... }, async ({ page, limit }) => {
  return makeRequest('GET', '/items', null, {
    page: page || 1,
    limit: limit || 5,
  });
});
```

### POST with body data
```typescript
server.registerTool('create_item', { ... }, async (args) => {
  return makeRequest('POST', '/items', args);
});
```

### Parallel data fetching
```typescript
server.registerTool('get_full_data', { ... }, async ({ id }) => {
  const [basic, details, extra] = await Promise.all([
    makeRequest('GET', `/items/${id}`),
    makeRequest('GET', `/items/${id}/details`),
    makeRequest('GET', `/items/${id}/extra`)
  ]);

  // Check for errors in any result
  if (basic.isError) return basic;
  if (details.isError) return details;
  if (extra.isError) return extra;

  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        basic: JSON.parse(basic.content[0].text),
        details: JSON.parse(details.content[0].text),
        extra: JSON.parse(extra.content[0].text)
      }, null, 2)
    }]
  };
});
```

### Optional parameters with conditional inclusion
```typescript
const params: Record<string, any> = { projectId };

if (startDate !== undefined) {
  params.startDate = startDate;
}
if (endDate !== undefined) {
  params.endDate = endDate;
}

return makeRequest('GET', '/transactions', null, params);
```

## Error Handling

The `makeRequest()` helper (index.ts:27-93) automatically handles:
- Non-OK HTTP responses (returns `isError: true`)
- Network errors (catches and formats)
- URL construction with query params
- JSON serialization/deserialization

Error response format:
```typescript
{
  content: [{ type: 'text', text: 'Error message' }],
  isError: true,
}
```

Success response format:
```typescript
{
  content: [{ type: 'text', text: 'JSON response data' }],
}
```

## Claude Desktop Integration (STDIO Mode)

Configure in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "joeapi-local": {
      "command": "node",
      "args": ["/absolute/path/to/joeMCP_fast/build/local-server.js"],
      "env": {
        "JOEAPI_BASE_URL": "http://localhost:8080"
      },
      "disabled": false
    }
  }
}
```

**Important:**
- Use absolute paths (not `~/` or relative paths)
- Build with `npm run build:stdio` before first use
- Restart Claude Desktop after config changes
- See `claude-desktop-config.example.json` for reference

## API Backend Requirements

This MCP server requires a running JoeAPI instance:
- Default: `https://joeapi.fly.dev` (production)
- Local dev: `http://localhost:8080`

JoeAPI must expose REST endpoints under `/api/v1/`:
- `/clients`, `/contacts`, `/proposals`, `/estimates`
- `/action-items`, `/project-details`, `/project-schedules`
- `/transactions`, `/job-balances`, `/cost-variance`
- `/search` (multi-type search with `?q=query&type=...`)

## Smithery HTTP Deployment

**Primary deployment mode** for production use.

**Configuration:**
- Set `apiBaseUrl` in Smithery dashboard to point to your JoeAPI instance
- Default: `https://joeapi.fly.dev`
- Config validated via `configSchema` export

**Development:**
```bash
npm run dev        # Opens interactive Smithery playground
npm run build:http # Build for deployment (automatic via Smithery CLI)
npm run start:http # Run built HTTP server locally
```

**Deployment:**
- Uses `@smithery/sdk` and `@smithery/cli`
- Build output in `.smithery/` directory
- Exports `configSchema` and default `createServer()` function
- Auto-deployed via Smithery platform

---

# FastMCP Implementation (Python)

The FastMCP implementation (`joeapi_server.py`) is the **recommended approach** for new deployments due to simpler syntax, built-in production features, and free cloud hosting.

## Build and Development Commands

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
export JOEAPI_BASE_URL=http://localhost:8080

# Run server
python joeapi_server.py
```

### FastMCP CLI
```bash
# Install CLI
pip install fastmcp

# Run server
fastmcp run joeapi_server.py:mcp --transport http --port 8000

# Inspect server (see tools without running)
fastmcp inspect joeapi_server.py:mcp
```

### Deploy to FastMCP Cloud
```bash
# 1. Push to GitHub
git add joeapi_server.py requirements.txt
git commit -m "Add FastMCP server"
git push

# 2. Go to fastmcp.cloud
# 3. Sign in with GitHub
# 4. Create project with entrypoint: joeapi_server.py:mcp
# 5. Set environment variable: JOEAPI_BASE_URL=https://joeapi.fly.dev
```

See `FASTMCP_DEPLOYMENT.md` for complete deployment guide.

## Architecture

### Core File
- `joeapi_server.py` - Complete FastMCP server (single file, ~600 lines)
  - Defines all 15+ tools using `@mcp.tool()` decorator
  - HTTP client using `httpx.AsyncClient`
  - Async/await pattern for all API calls
  - SSE streaming support for async-agent tool

### Tool Definition Pattern

FastMCP uses a decorator-based pattern with automatic schema generation:

```python
@mcp.tool()
async def list_clients(page: int = 1, limit: int = 5) -> Dict[str, Any]:
    """
    Retrieve a paginated list of clients.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 5, max: 100)

    Returns:
        Paginated list of clients with their details
    """
    return await make_request("GET", "/clients", params={"page": page, "limit": limit})
```

**Key features:**
- Type hints define parameter types
- Docstrings become tool descriptions
- Return types validated automatically
- No manual schema definitions needed

### Helper Function Pattern

All API calls use a centralized `make_request()` helper:

```python
async def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make HTTP request to JoeAPI backend with error handling"""
    url = f"{API_BASE_URL}/api/v1{endpoint}"

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.request(method, url, json=data, params=params)
        response.raise_for_status()
        return response.json()
```

### Available Tools

**15+ tools across 7 categories:**

1. **Clients & Contacts**
   - `list_clients`, `create_client`
   - `list_contacts`, `create_contact`

2. **Proposals**
   - `list_proposals`, `create_proposal`, `find_proposal`

3. **Projects**
   - `find_project`, `get_project_details`, `list_schedules`

4. **Action Items**
   - `find_action_items`

5. **Financial**
   - `get_financials` (parallel fetching of job balances + cost variance)
   - `get_transactions` (with optional date filtering)

6. **Search**
   - `search` (generic multi-type search across all entities)

7. **Async Agent**
   - `async_agent` (SSE streaming for complex multi-step workflows)

### Special Implementation: Async Agent Tool

The `async_agent` tool uses Server-Sent Events (SSE) streaming:

```python
@mcp.tool()
async def async_agent(prompt: str) -> Dict[str, Any]:
    """Delegate complex workflows to async-agent with real-time progress"""
    async with httpx.AsyncClient(timeout=360) as client:
        async with client.stream("POST", ASYNC_AGENT_URL, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])

                    if event_data["type"] == "progress":
                        print(f"Progress: {event_data['message']}")
                    elif event_data["type"] == "complete":
                        return event_data["data"]
```

**Features:**
- Async streaming with `httpx.AsyncClient.stream()`
- 6-minute timeout for long-running workflows
- Real-time progress logging via `print()`
- Graceful error handling

### Special Implementation: Parallel Data Fetching

The `get_financials` and `list_schedules` tools use `asyncio.gather()` for parallel requests:

```python
@mcp.tool()
async def get_financials(projectId: str) -> Dict[str, Any]:
    """Get comprehensive financial data with parallel fetching"""
    import asyncio

    job_balances, cost_variance = await asyncio.gather(
        make_request("GET", "/job-balances", params={"projectId": projectId}),
        make_request("GET", "/cost-variance", params={"projectId": projectId})
    )

    return {
        "jobBalances": job_balances,
        "costVariance": cost_variance
    }
```

## Configuration

**Environment Variables:**
- `JOEAPI_BASE_URL` - JoeAPI backend URL (default: `https://joeapi.fly.dev`)
- `JOEAPI_API_KEY` - Optional API key for authentication
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)

**Set in FastMCP Cloud dashboard** under Project Settings → Environment Variables

**Set locally** via shell or `.env` file:
```bash
export JOEAPI_BASE_URL=http://localhost:8080
export JOEAPI_API_KEY=your_api_key_here
export REQUEST_TIMEOUT=60
```

## Adding New Tools

1. **Add tool function** in `joeapi_server.py`:
```python
@mcp.tool()
async def my_new_tool(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """
    Description of what this tool does.

    Args:
        param1: Description of param1
        param2: Optional description of param2

    Returns:
        Description of return value
    """
    return await make_request("GET", "/endpoint", params={
        "param1": param1,
        **({"param2": param2} if param2 else {})
    })
```

2. **Test locally**:
```bash
python joeapi_server.py
# or
fastmcp run joeapi_server.py:mcp --transport http
```

3. **Deploy** - Just push to GitHub:
```bash
git add joeapi_server.py
git commit -m "Add my_new_tool"
git push  # Auto-deploys to FastMCP Cloud
```

## FastMCP Cloud Features

- **Free hosting** for personal servers
- **Automatic deployment** on git push
- **PR preview URLs** for testing changes
- **Built-in authentication** (OAuth, organization-only)
- **Real-time logs** and monitoring
- **Environment variable management**
- **Custom domains** (team plans)

## Comparison: TypeScript vs FastMCP

| Feature | TypeScript | FastMCP (Python) |
|---------|-----------|------------------|
| **Framework** | `@modelcontextprotocol/sdk` | FastMCP |
| **Language** | TypeScript | Python |
| **Schema Definition** | Manual Zod schemas | Auto-generated from type hints |
| **Lines of Code** | ~1013 lines | ~600 lines |
| **Deployment** | Smithery | FastMCP Cloud (free) |
| **Authentication** | Manual | Built-in OAuth |
| **Async Patterns** | Promises | async/await |
| **HTTP Client** | `fetch` | `httpx` |
| **Learning Curve** | Moderate | Low (Pythonic) |
| **Best For** | Existing TS projects | New deployments, Python devs |

## Dependencies

### TypeScript Implementation
- `@modelcontextprotocol/sdk` (^1.21.1) - MCP protocol implementation
- `@smithery/sdk` (^1.6.4) - Smithery HTTP transport
- `@smithery/cli` (^1.4.0) - Smithery CLI tools
- `zod` (^3.25.76) - Runtime type validation and schema definition
- `tsx` (^4.20.6) - TypeScript execution for development
- `typescript` (^5.9.3) - TypeScript compilation

### Python/FastMCP Implementation
- `fastmcp` (>=2.0.0) - FastMCP framework for building MCP servers
- `httpx` (>=0.27.0) - Async HTTP client for API requests
