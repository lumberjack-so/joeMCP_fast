# JoeAPI MCP Server - FastMCP Edition

FastMCP implementation of the JoeAPI MCP server for construction management.

## Quick Start

### 1. Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variable
export JOEAPI_BASE_URL=http://localhost:8080

# Run server
python joeapi_server.py
```

Server runs on `http://localhost:8000/mcp`

### 2. Deploy to FastMCP Cloud

```bash
# Push to GitHub
git add joeapi_server.py requirements.txt
git commit -m "Deploy FastMCP server"
git push

# Then:
# 1. Go to https://fastmcp.cloud
# 2. Sign in with GitHub
# 3. Create new project from your repository
# 4. Entrypoint: joeapi_server.py:mcp
# 5. Set JOEAPI_BASE_URL environment variable
```

Your server will be available at `https://YOUR-PROJECT.fastmcp.app/mcp`

## Features

### 15+ Tools Available

1. **Clients**: `list_clients`, `create_client`
2. **Contacts**: `list_contacts`, `create_contact`
3. **Proposals**: `list_proposals`, `create_proposal`, `find_proposal`
4. **Projects**: `find_project`, `get_project_details`, `list_schedules`
5. **Action Items**: `find_action_items`
6. **Financial**: `get_financials`, `get_transactions`
7. **Search**: `search` (multi-type search)
8. **Async Agent**: `async_agent` (complex workflows with SSE streaming)

### Key Capabilities

- **Async HTTP requests** using `httpx`
- **Parallel data fetching** with `asyncio.gather()`
- **SSE streaming** for real-time progress updates
- **Environment-based configuration**
- **Automatic error handling**
- **Type-safe with Python type hints**

## Configuration

Set via environment variables:

- `JOEAPI_BASE_URL` - JoeAPI backend URL (default: `https://joeapi.fly.dev`)
- `JOEAPI_API_KEY` - Optional API key
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)

## Usage Examples

### Connect from Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "joeapi-fastmcp": {
      "url": "https://YOUR-PROJECT.fastmcp.app/mcp"
    }
  }
}
```

### Call from Python

```python
from fastmcp import Client
import asyncio

async def main():
    client = Client("https://YOUR-PROJECT.fastmcp.app/mcp")

    async with client:
        # List clients
        result = await client.call_tool("list_clients", {"limit": 5})
        print(result)

        # Search projects
        result = await client.call_tool("find_project", {"query": "residential"})
        print(result)

asyncio.run(main())
```

### Inspect Available Tools

```bash
# Install FastMCP CLI
pip install fastmcp

# View all tools
fastmcp inspect joeapi_server.py:mcp
```

## Architecture

### Single File Design

All code is in `joeapi_server.py` (~600 lines):

- **Configuration** - Environment variables loaded at startup
- **Helper function** - `make_request()` handles all API calls
- **Tool definitions** - Each tool decorated with `@mcp.tool()`
- **Main entry** - HTTP server runs on port 8000

### Tool Pattern

```python
@mcp.tool()
async def tool_name(param: str, optional: int = 0) -> Dict[str, Any]:
    """Tool description shown to LLM"""
    return await make_request("GET", "/endpoint", params={"param": param})
```

- Type hints → parameter types
- Docstrings → tool descriptions
- Automatic schema generation
- Async by default

## Migration from TypeScript

### What Changed

| Aspect | TypeScript | FastMCP (Python) |
|--------|-----------|------------------|
| **Lines of code** | ~1013 | ~600 |
| **Tool registration** | `server.registerTool(...)` | `@mcp.tool()` decorator |
| **Schema** | Manual Zod objects | Auto from type hints |
| **Async** | Promises | async/await |
| **HTTP client** | `fetch` | `httpx.AsyncClient` |
| **Deployment** | Smithery | FastMCP Cloud (free) |

### What Stayed the Same

- All 15+ tools with identical functionality
- Same API endpoints and parameters
- Same error handling patterns
- Same environment variable names
- Same async-agent SSE streaming

## Documentation

- **Full deployment guide**: See `FASTMCP_DEPLOYMENT.md`
- **Architecture details**: See `CLAUDE.md` (FastMCP section)
- **FastMCP docs**: https://gofastmcp.com
- **FastMCP Cloud**: https://fastmcp.cloud

## Development

### Add a New Tool

1. Add function with `@mcp.tool()` decorator:

```python
@mcp.tool()
async def new_tool(param: str) -> Dict[str, Any]:
    """What this tool does"""
    return await make_request("GET", "/new-endpoint", params={"param": param})
```

2. Test locally:
```bash
python joeapi_server.py
```

3. Deploy:
```bash
git add joeapi_server.py
git commit -m "Add new_tool"
git push  # Auto-deploys to FastMCP Cloud
```

### Run Tests

```bash
# Start server in one terminal
python joeapi_server.py

# In another terminal, test with FastMCP client
python -c "
from fastmcp import Client
import asyncio

async def test():
    client = Client('http://localhost:8000/mcp')
    async with client:
        result = await client.call_tool('list_clients', {'limit': 1})
        print(result)

asyncio.run(test())
"
```

## Support

- **FastMCP Issues**: https://github.com/jlowin/fastmcp/issues
- **FastMCP Cloud Support**: https://fastmcp.cloud/support
- **JoeAPI Issues**: Your JoeAPI repository

## License

Same as JoeAPI project.
