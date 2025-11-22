# FastMCP Cloud Deployment Guide

This guide covers deploying the JoeAPI MCP server to FastMCP Cloud.

## Overview

FastMCP Cloud is a hosting platform optimized for FastMCP servers, providing:
- **Free hosting** for personal servers
- **Automatic deployment** from GitHub
- **Secure URLs** with optional authentication
- **Automatic dependency installation**
- **PR preview deployments**

## Prerequisites

1. **GitHub Account** - Sign up at [github.com](https://github.com)
2. **FastMCP Cloud Account** - Sign in at [fastmcp.cloud](https://fastmcp.cloud) with GitHub
3. **GitHub Repository** - Create a repository and push your code

## Quick Start

### 1. Push to GitHub

If you haven't already, initialize a git repository and push to GitHub:

```bash
# Initialize git repository (if not already done)
git init
git add joeapi_server.py requirements.txt

# Create initial commit
git commit -m "Add FastMCP JoeAPI server"

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Deploy to FastMCP Cloud

1. Go to [fastmcp.cloud](https://fastmcp.cloud)
2. Sign in with your GitHub account
3. Click **"New Project"**
4. Select your GitHub repository
5. Configure the project:
   - **Name**: `joeapi-mcp` (or your preferred name)
   - **Entrypoint**: `joeapi_server.py:mcp`
   - **Authentication**: Choose public or organization-only

6. Click **"Deploy"**

FastMCP Cloud will:
- Clone your repository
- Install dependencies from `requirements.txt`
- Build and deploy your server
- Provide a URL like `https://joeapi-mcp.fastmcp.app/mcp`

### 3. Configure Environment Variables

Set environment variables in the FastMCP Cloud dashboard:

**Required:**
- `JOEAPI_BASE_URL` - Base URL for JoeAPI backend
  - Production: `https://joeapi.fly.dev`
  - Local dev: `http://localhost:8080`

**Optional:**
- `JOEAPI_API_KEY` - API key for JoeAPI authentication (if required)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: 30)

### 4. Test Your Server

Once deployed, you can:

1. **Chat with your server** in the FastMCP Cloud interface
2. **Connect from Claude Desktop** by adding to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "joeapi-fastmcp": {
      "url": "https://YOUR-PROJECT.fastmcp.app/mcp"
    }
  }
}
```

3. **Call from Python** using the FastMCP client:

```python
from fastmcp import Client
import asyncio

async def test_server():
    client = Client("https://YOUR-PROJECT.fastmcp.app/mcp")

    async with client:
        # List available tools
        tools = await client.list_tools()
        print("Available tools:", [t.name for t in tools])

        # Call a tool
        result = await client.call_tool("list_clients", {"limit": 3})
        print("Clients:", result)

asyncio.run(test_server())
```

## Local Development

Test your server locally before deploying:

### Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```bash
# Set environment variables
export JOEAPI_BASE_URL=http://localhost:8080

# Run server with HTTP transport
python joeapi_server.py
```

The server will start on `http://localhost:8000/mcp`

### Test with FastMCP CLI

```bash
# Install FastMCP CLI
pip install fastmcp

# Run server with CLI
fastmcp run joeapi_server.py:mcp --transport http --port 8000

# Inspect server (see tools without running)
fastmcp inspect joeapi_server.py:mcp
```

## Continuous Deployment

FastMCP Cloud automatically redeploys when you push to your `main` branch:

```bash
# Make changes to joeapi_server.py
git add joeapi_server.py
git commit -m "Add new tool for estimates"
git push

# FastMCP Cloud will automatically rebuild and redeploy
```

## Pull Request Previews

Every pull request gets a unique preview URL:

1. Create a new branch and make changes
2. Push the branch and create a PR
3. FastMCP Cloud deploys a preview at `https://pr-123-YOUR-PROJECT.fastmcp.app/mcp`
4. Test changes before merging to main

## Authentication

FastMCP Cloud supports multiple authentication methods:

### Organization-Only Access

In the project settings, enable **"Organization Only"** to require authentication:
- Only members of your GitHub organization can access the server
- Automatic OAuth flow handles authentication
- No code changes required

### Custom Authentication

Add custom authentication in your server code:

```python
from fastmcp import FastMCP
from fastmcp.auth import BearerAuth

mcp = FastMCP("JoeAPI Construction Management")

# Add bearer token authentication
@mcp.auth
async def authenticate(token: str) -> dict:
    """Validate bearer token and return user context"""
    if token == os.getenv("API_SECRET_TOKEN"):
        return {"user": "authorized"}
    raise ValueError("Invalid token")
```

## Monitoring and Logs

View logs in the FastMCP Cloud dashboard:

1. Go to your project
2. Click **"Logs"** tab
3. View real-time logs including:
   - Tool calls
   - API requests
   - Errors and exceptions
   - Progress messages (from `print()` statements)

## Troubleshooting

### Server Not Starting

**Check logs** for errors during startup:
- Missing dependencies → Update `requirements.txt`
- Import errors → Verify Python version compatibility
- Environment variable errors → Set required variables in dashboard

### Tool Calls Failing

**Common issues:**

1. **JoeAPI not accessible**
   - Verify `JOEAPI_BASE_URL` is correct
   - Check if JoeAPI is running and accessible
   - Test with: `curl https://joeapi.fly.dev/health`

2. **Authentication errors**
   - Set `JOEAPI_API_KEY` if JoeAPI requires authentication
   - Verify API key is valid

3. **Timeout errors**
   - Increase `REQUEST_TIMEOUT` for slow endpoints
   - Check network connectivity

### Connection from Claude Desktop

If Claude Desktop can't connect:

1. **Verify URL** - Use the full URL from FastMCP Cloud dashboard
2. **Check authentication** - Ensure authentication is disabled or properly configured
3. **Restart Claude Desktop** - Close completely and reopen
4. **Check logs** - View FastMCP Cloud logs for connection attempts

## Cost and Limits

**Free Tier:**
- Personal servers are **free forever**
- Unlimited tool calls
- Unlimited deployments
- Community support

**Team Pricing:**
- Pay-as-you-go for team/organization servers
- See [fastmcp.cloud/pricing](https://fastmcp.cloud/pricing) for details

## Next Steps

1. **Add more tools** - Extend `joeapi_server.py` with additional JoeAPI endpoints
2. **Add authentication** - Implement custom auth if needed
3. **Monitor usage** - Check logs and metrics in FastMCP Cloud dashboard
4. **Share with team** - Add team members to your GitHub organization for access

## Resources

- **FastMCP Documentation**: [gofastmcp.com](https://gofastmcp.com/)
- **FastMCP Cloud**: [fastmcp.cloud](https://fastmcp.cloud)
- **FastMCP GitHub**: [github.com/jlowin/fastmcp](https://github.com/jlowin/fastmcp)
- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **FastMCP Tutorials**: [Build MCP Servers in Python](https://mcpcat.io/guides/building-mcp-server-python-fastmcp/)

## Support

- **FastMCP Community**: GitHub Discussions on [jlowin/fastmcp](https://github.com/jlowin/fastmcp)
- **FastMCP Cloud Support**: [fastmcp.cloud/support](https://fastmcp.cloud)
- **JoeAPI Issues**: Your JoeAPI repository issue tracker
