# JoeAPI MCP Server

Model Context Protocol (MCP) server for JoeAPI construction management system. Exposes construction management tools to Claude and other AI assistants.

## Overview

This MCP server provides:
- **18 pre-built workflows** for common construction management tasks
- **60+ individual tools** for direct API access (CRUD operations)
- **Multi-transport support**: Smithery (cloud) and STDIO (local)

## Architecture

```
mcp/
├── index.ts                           # Main MCP server (Smithery + STDIO)
├── local-server.ts                    # STDIO transport runner
├── claude-desktop-config.example.json # Claude Desktop config
├── README.md                          # This file
└── server.ts                          # Legacy (deprecated)

mcp-build/                             # Compiled JavaScript (production)
├── index.js                           # Compiled server
├── local-server.js                    # Compiled STDIO runner
└── *.d.ts                             # TypeScript definitions
```

## Deployment Options

### 1. Smithery (Cloud) - **EXISTING**

Your MCP server is already deployed on Smithery for cloud access.

**Access:** Via Smithery marketplace
**URL:** `https://smithery.ai/server/@your-username/joeapi`
**Transport:** HTTP
**Use case:** Remote access, team collaboration

### 2. Local STDIO - **THIS SETUP**

Run MCP server locally on your machine for development/testing.

**Transport:** STDIO (Standard Input/Output)
**Use case:** Local development, faster iteration, offline work

---

## Local STDIO Setup

### Prerequisites

1. **JoeAPI running locally:**
   ```bash
   npm run dev  # Start JoeAPI on http://localhost:8080
   ```

2. **Build MCP server:**
   ```bash
   npm run mcp:build
   ```

3. **Configure Claude Desktop:**
   - Copy `mcp/claude-desktop-config.example.json`
   - Update the `command` path to match your installation
   - Add to Claude Desktop config

### Option A: Development Mode (TypeScript)

**For rapid development with auto-recompile:**

```bash
npm run mcp:local
```

This runs `tsx mcp/local-server.ts` - TypeScript executed directly (no build needed).

### Option B: Production Mode (Compiled JavaScript)

**For production use:**

```bash
# Build once
npm run mcp:build

# Run compiled version
npm run mcp:start
```

This runs `node mcp-build/local-server.js` - faster startup, production-ready.

---

## Claude Desktop Configuration

### Step 1: Find Claude Config Directory

**macOS:**
```bash
~/Library/Application Support/Claude/
```

**Windows:**
```
%APPDATA%\Claude\
```

**Linux:**
```
~/.config/Claude/
```

### Step 2: Edit `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "joeapi-local": {
      "command": "node",
      "args": [
        "/ABSOLUTE/PATH/TO/joeapi/mcp-build/local-server.js"
      ],
      "env": {
        "JOEAPI_BASE_URL": "http://localhost:8080"
      },
      "disabled": false
    }
  }
}
```

**Important:**
- Use **absolute paths** (not relative like `~/` or `./`)
- Change `/ABSOLUTE/PATH/TO/joeapi/` to your actual path
- Example: `/Users/joe/dev/joeapi/mcp-build/local-server.js`

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop. The MCP server will connect automatically.

### Step 4: Verify Connection

In Claude Desktop, type:
```
Can you use the find_workflow tool?
```

If connected, Claude will have access to all JoeAPI tools.

---

## Available Tools

### Workflow Discovery (ALWAYS START HERE!)

**find_workflow** - Discover pre-built workflows
- Set `autoExecute: false` to see ALL 18 workflows
- Set `autoExecute: true` with workflow name to get step-by-step instructions

### 18 Pre-Built Workflows

1. `win_loss_rate` - Calculate proposal win/loss statistics
2. `sales_pipeline` - Analyze active proposals in pipeline
3. `work_in_process_report` - WIP report for active projects
4. `job_costing_detail` - Detailed job costing analysis
5. `project_profitability` - Profit analysis by project
6. `cost_variance_analysis` - Actual vs. estimated cost variance
7. `cash_flow_forecast` - Project cash flow projections
8. `schedule_variance_analysis` - Schedule delays and impacts
9. `client_portal_update` - Generate client progress updates
10. `subcontractor_performance` - Analyze subcontractor metrics
11. `material_tracking` - Track material costs and usage
12. `labor_productivity` - Analyze labor efficiency
13. `cost_per_square_foot` - Calculate $/sqft by trade
14. `change_order_tracking` - Track change orders/revisions
15. `upgrade_pricing` - Price client upgrade requests
16. `update_schedule` - Extend/adjust project schedules
17. `plan_takeoff` - Estimate from building plans
18. `estimate_from_previous` - Create estimate from past job

### 60+ Individual Tools (Categories)

- **Clients** - CRUD operations for clients
- **Contacts** - Manage client contacts
- **SubContractors** - Subcontractor management
- **Proposals** - Create and track proposals
- **ProposalLines** - Line items within proposals
- **Estimates** - Project estimates
- **ProjectManagements** - Active project data
- **ProjectSchedules** - Project timelines
- **ProjectScheduleTasks** - Individual tasks
- **ActionItems** - Track action items with:
  - Comments
  - Supervisors
  - Cost changes
  - Schedule changes
- **Transactions** - QuickBooks transaction data
- **JobBalances** - Current job balances
- **CostVariance** - Cost variance analysis
- **Invoices** - Invoice management
- **ScheduleRevisions** - Schedule change tracking
- **ProjectDetails** - Comprehensive project data
- **ProposalPipeline** - Pipeline analytics
- **EstimateRevisions** - Estimate change history
- **CostRevisions** - Cost revision tracking
- **Deposits** - Deposit/retainer management
- **ProposalTemplatePricing** - Standard pricing templates

---

## Environment Variables

### Required

```bash
JOEAPI_BASE_URL=http://localhost:8080  # Local JoeAPI server
```

### Optional (if JoeAPI requires auth)

```bash
JOEAPI_API_KEY=your_api_key           # API key for JoeAPI
JOEAPI_USER_ID=1                      # Dev user ID
```

Set these in:
1. **Claude Desktop config** (recommended):
   ```json
   "env": {
     "JOEAPI_BASE_URL": "http://localhost:8080"
   }
   ```

2. **Shell environment** (alternative):
   ```bash
   export JOEAPI_BASE_URL=http://localhost:8080
   ```

---

## Troubleshooting

### MCP Server Not Connecting

**1. Check JoeAPI is running:**
```bash
curl http://localhost:8080/health
# Should return: {"status":"healthy",...}
```

**2. Check MCP server builds:**
```bash
npm run mcp:build
# Should complete without errors
```

**3. Check Claude Desktop logs:**

**macOS:**
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows:**
```powershell
Get-Content $env:APPDATA\Claude\logs\mcp*.log -Wait
```

**4. Test MCP server manually:**
```bash
npm run mcp:local
# Should output: "JoeAPI MCP Server running locally"
# Press Ctrl+C to stop
```

### Tools Not Appearing in Claude

**1. Verify config path is absolute:**
```json
"args": ["/Users/joe/dev/joeapi/mcp-build/local-server.js"]
```
Not: `["~/dev/joeapi/mcp-build/local-server.js"]` ❌

**2. Check disabled flag:**
```json
"disabled": false  // Should be false
```

**3. Restart Claude Desktop:**
- Close completely (Cmd+Q on macOS)
- Reopen

**4. Check for errors in MCP logs**

### JoeAPI Connection Errors

**Error:** `JoeAPI error (401)`
- JoeAPI requires authentication
- Add API key or dev user ID to config

**Error:** `JoeAPI error (404)`
- Endpoint not found
- Check JoeAPI version matches MCP server

**Error:** `ECONNREFUSED`
- JoeAPI not running
- Start with: `npm run dev`

---

## Development

### Adding New Tools

1. **Edit `mcp/index.ts`:**
   ```typescript
   {
     name: 'my_new_tool',
     description: 'Description of tool',
     inputSchema: {
       type: 'object',
       properties: {
         param1: { type: 'string', description: '...' }
       },
       required: ['param1']
     }
   }
   ```

2. **Add handler in `CallToolRequest`:**
   ```typescript
   case 'my_new_tool': {
     const { param1 } = args as { param1: string };
     result = await callJoeAPI(baseUrl, `/api/v1/endpoint`);
     break;
   }
   ```

3. **Rebuild:**
   ```bash
   npm run mcp:build
   ```

4. **Restart Claude Desktop**

### Adding New Workflows

1. **Add to `prompts` array in `mcp/index.ts`:**
   ```typescript
   {
     name: 'my_workflow',
     description: 'Brief description',
     arguments: [...],
     prompt: 'WORKFLOW: My Workflow\n\nPURPOSE: ...\n\nSTEPS:\n1. ...'
   }
   ```

2. **Rebuild and restart**

---

## Scripts Reference

```bash
# Development
npm run mcp:local     # Run TypeScript directly (tsx)
npm run dev          # Run JoeAPI server

# Production
npm run mcp:build    # Compile TypeScript → JavaScript
npm run mcp:start    # Run compiled JavaScript

# Both
npm run verify-db    # Test database connection
```

---

## Comparison: Smithery vs Local STDIO

| Feature | Smithery (Cloud) | Local STDIO |
|---------|------------------|-------------|
| **Setup** | Already deployed | Requires local setup |
| **Access** | Remote, anywhere | Local machine only |
| **Speed** | Network latency | Instant (local) |
| **Availability** | Always on | Requires JoeAPI running |
| **Updates** | Auto-deployed | Manual build required |
| **Collaboration** | Team access | Single user |
| **Best for** | Production, team | Development, testing |

---

## Support

- **MCP SDK Docs**: https://modelcontextprotocol.io
- **Claude Desktop MCP Guide**: https://docs.claude.com/docs/mcp
- **JoeAPI Issues**: Check GitHub repo
- **MCP Server Code**: `mcp/index.ts`
