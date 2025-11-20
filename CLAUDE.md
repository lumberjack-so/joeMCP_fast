# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for JoeAPI, a construction management system. It exposes REST API endpoints as MCP tools, making construction management data accessible to AI assistants like Claude.

## Build and Development Commands

### Building
```bash
npm run build        # Compile TypeScript to JavaScript (output: ./build/)
```

### Running the Server

**Development mode (TypeScript with tsx):**
```bash
npm run dev         # Runs local-server.ts directly with tsx
```

**Production mode (compiled JavaScript):**
```bash
npm run start       # Runs build/local-server.js with node
```

### Testing
To test the MCP server manually, run it and interact via STDIO. The server expects MCP protocol messages on stdin and responds on stdout.

## Architecture

### Core Files
- `index.ts` - Main MCP server implementation containing all tool definitions and handlers
- `local-server.ts` - Minimal wrapper that imports and runs index.ts (adds logging message)
- `build/` - Compiled JavaScript output directory

### Transport Layer
This MCP server uses **STDIO transport** exclusively. It communicates via standard input/output, making it suitable for local Claude Desktop integration.

### API Wrapper Pattern
The server follows a consistent pattern:
1. **Tool Definition**: Each tool is defined in `ListToolsRequestSchema` handler with name, description, and JSON schema for inputs
2. **Request Handler**: Switch statement in `CallToolRequestSchema` handler routes tool calls to appropriate API endpoints
3. **API Helper**: `makeRequest()` function handles all HTTP communication with JoeAPI backend

### Tool Categories
Tools are organized into logical groups (see index.ts:105-518):
1. **Clients & Contacts** - CRUD operations for clients and contacts
2. **Proposals & Estimates** - Proposal management and line items
3. **Action Items** - Task tracking with comments, supervisors, cost/schedule changes
4. **Projects** - Project management, schedules, and comprehensive search
5. **Financial** - Transaction summaries, job balances, cost variance
6. **Async Agent** - Delegates complex workflows to external async-agent service

### Special Tools

**`search` tool (index.ts:625-712)**
This is a compound tool that performs multi-step operations:
- Searches for a project by query string
- Fetches comprehensive data in parallel: transactions, action items, estimates, schedule revisions, estimate revisions
- Aggregates results into a single formatted response
- Demonstrates the pattern for creating complex multi-API workflows

**`async` tool (index.ts:741-821)**
Delegates to external async-agent service at `https://joeapi-async-agent.fly.dev`:
- 2-minute timeout with AbortController
- Webhook-based invocation
- Optional callId tracking
- Used for complex multi-step workflows requiring orchestration

### Configuration

**Environment Variables:**
- `JOEAPI_BASE_URL` - Base URL for JoeAPI (defaults to `https://joeapi.fly.dev`)
  - For local development: `http://localhost:8080`
  - Configure in Claude Desktop config or shell environment

**TypeScript Configuration:**
- Target: ES2022
- Module: Node16 with ESM
- Strict mode enabled
- Output directory: `./build`

## Adding New Tools

To add a new tool:

1. **Add tool definition** in `ListToolsRequestSchema` handler (index.ts:108):
```typescript
{
  name: 'my_new_tool',
  description: 'Clear description of what this tool does',
  inputSchema: {
    type: 'object',
    properties: {
      paramName: {
        type: 'string',
        description: 'Parameter description',
      },
    },
    required: ['paramName'],
  },
}
```

2. **Add handler** in `CallToolRequestSchema` switch statement (index.ts:539):
```typescript
case 'my_new_tool':
  return makeRequest('GET', '/api-endpoint', null, {
    paramName: args.paramName,
  });
```

3. **Rebuild**: `npm run build`
4. **Restart Claude Desktop** to pick up the new tool

## Common Patterns

### Simple GET with query params
```typescript
case 'list_items':
  return makeRequest('GET', '/items', null, {
    page: args.page || 1,
    limit: args.limit || 5,
  });
```

### POST with body data
```typescript
case 'create_item':
  return makeRequest('POST', '/items', args);
```

### Compound operations (multiple API calls)
```typescript
case 'get_full_data': {
  const basic = await makeRequest('GET', `/items/${args.id}`);
  const details = await makeRequest('GET', `/items/${args.id}/details`);

  return {
    content: [{
      type: 'text',
      text: `BASIC:\n${basic.content[0].text}\n\nDETAILS:\n${details.content[0].text}`,
    }],
  };
}
```

### Parallel fetching
```typescript
const [data1, data2, data3] = await Promise.all([
  makeRequest('GET', '/endpoint1'),
  makeRequest('GET', '/endpoint2'),
  makeRequest('GET', '/endpoint3'),
]);
```

## Error Handling

The `makeRequest()` helper automatically handles:
- Non-OK HTTP responses (returns `isError: true`)
- Network errors (catches and formats)
- Missing arguments (type-guarded in handler)

Error responses follow the format:
```typescript
{
  content: [{ type: 'text', text: 'Error message' }],
  isError: true,
}
```

## Claude Desktop Integration

Users configure this server in `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "joeapi-local": {
      "command": "node",
      "args": ["/absolute/path/to/joemcp/build/local-server.js"],
      "env": {
        "JOEAPI_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
```

**Important**: Paths must be absolute (not relative like `~/`)

## API Backend Requirements

This MCP server requires a running JoeAPI instance:
- Default: `https://joeapi.fly.dev` (production)
- Local dev: `http://localhost:8080`

The JoeAPI must expose REST endpoints under `/api/v1/` including:
- `/clients`, `/contacts`, `/proposals`, `/estimates`
- `/action-items`, `/project-details`, `/project-schedules`
- `/transactions`, `/job-balances`, `/cost-variance`
- `/search` (project search endpoint)

## Smithery HTTP Deployment

This server is deployed on Smithery for remote HTTP access.

**Configuration:**
- Set `apiBaseUrl` in Smithery dashboard to point to your JoeAPI instance
- Default: `https://joeapi.fly.dev`
- For testing: Use local JoeAPI or development instance

**Development with Smithery:**
```bash
npm run dev        # Opens interactive playground
npm run build:http # Build for Smithery deployment
npm run start:http # Run built HTTP server
```

**STDIO Mode (Backward Compatibility):**
```bash
npm run build:stdio # Compile TypeScript
npm run start:stdio # Run STDIO transport
npm run dev:stdio   # Development with tsx
```

## Dependencies

- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `zod` - Runtime type validation (imported but not actively used in current code)
- `tsx` - TypeScript execution for development mode
- `typescript` - Compilation
