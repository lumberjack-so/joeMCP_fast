#!/usr/bin/env python3
"""
JoeAPI MCP Server - FastMCP Implementation

Model Context Protocol server for JoeAPI construction management system.
Exposes construction management tools via FastMCP for deployment to FastMCP Cloud.
"""

import os
from typing import Optional, Dict, Any
import httpx
from fastmcp import FastMCP

# Initialize FastMCP server with extended timeout for long-running operations
mcp = FastMCP(
    "JoeAPI Construction Management",
    dependencies=["httpx"],
    request_timeout=600  # 10 minutes for long-running async_agent operations
)

# Configuration from environment variables
API_BASE_URL = os.getenv("JOEAPI_BASE_URL", "https://joeapi.fly.dev")
API_KEY = os.getenv("JOEAPI_API_KEY")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))


# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make HTTP request to JoeAPI backend.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path (e.g., '/clients')
        data: Request body data for POST/PUT
        params: Query parameters

    Returns:
        JSON response data

    Raises:
        httpx.HTTPError: If request fails
    """
    # Ensure endpoint starts with /
    if not endpoint.startswith('/'):
        endpoint = f'/{endpoint}'

    url = f"{API_BASE_URL}/api/v1{endpoint}"

    # Prepare headers
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    # Filter out None values from params
    if params:
        params = {k: v for k, v in params.items() if v is not None}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, params=params, headers=headers)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data, params=params, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise Exception(f"API Error {e.response.status_code}: {error_detail}")
        except httpx.RequestError as e:
            raise Exception(f"Network Error: {str(e)}")


# ==========================================
# 1. CLIENTS & CONTACTS TOOLS
# ==========================================

@mcp.tool()
async def list_clients(
    page: int = 1,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Retrieve a paginated list of clients.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 5, max: 100)

    Returns:
        Paginated list of clients with their details
    """
    return await make_request("GET", "/clients", params={"page": page, "limit": limit})


@mcp.tool()
async def create_client(
    Name: str,
    EmailAddress: str,
    CompanyName: str,
    Phone: str
) -> Dict[str, Any]:
    """
    Create a new client record.

    Args:
        Name: Client name
        EmailAddress: Client email address
        CompanyName: Company name
        Phone: Phone number

    Returns:
        Created client record
    """
    return await make_request("POST", "/clients", data={
        "Name": Name,
        "EmailAddress": EmailAddress,
        "CompanyName": CompanyName,
        "Phone": Phone
    })


@mcp.tool()
async def list_contacts(limit: int = 5) -> Dict[str, Any]:
    """
    Retrieve a list of contacts.

    Args:
        limit: Items per page (default: 5)

    Returns:
        List of contacts
    """
    return await make_request("GET", "/contacts", params={"limit": limit})


@mcp.tool()
async def create_contact(
    FirstName: str,
    LastName: str,
    Email: str,
    Phone: str,
    ClientId: str
) -> Dict[str, Any]:
    """
    Create a new contact record.

    Args:
        FirstName: Contact first name
        LastName: Contact last name
        Email: Contact email
        Phone: Contact phone number
        ClientId: Associated client GUID

    Returns:
        Created contact record
    """
    return await make_request("POST", "/contacts", data={
        "FirstName": FirstName,
        "LastName": LastName,
        "Email": Email,
        "Phone": Phone,
        "ClientId": ClientId
    })


# ==========================================
# 2. PROPOSALS TOOLS
# ==========================================

@mcp.tool()
async def list_proposals(
    page: int = 1,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Retrieve a paginated list of proposals.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 5)

    Returns:
        Paginated list of proposals
    """
    return await make_request("GET", "/proposals", params={"page": page, "limit": limit})


@mcp.tool()
async def create_proposal(
    Title: str,
    Description: str,
    ClientId: str,
    Amount: float
) -> Dict[str, Any]:
    """
    Create a new proposal.

    Args:
        Title: Proposal title
        Description: Proposal description
        ClientId: Associated client GUID
        Amount: Proposal amount

    Returns:
        Created proposal record
    """
    return await make_request("POST", "/proposals", data={
        "Title": Title,
        "Description": Description,
        "ClientId": ClientId,
        "Amount": Amount
    })


@mcp.tool()
async def find_proposal(
    query: str,
    projectId: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for proposals by proposal number, title, or description.

    Args:
        query: Search query to find proposals
        projectId: Optional project GUID to filter proposals by project

    Returns:
        Matching proposals
    """
    params = {"q": query, "type": "proposal"}
    if projectId:
        params["projectId"] = projectId

    return await make_request("GET", "/search", params=params)


# ==========================================
# 3. PROJECTS TOOLS
# ==========================================

@mcp.tool()
async def find_project(query: str) -> Dict[str, Any]:
    """
    Search for projects by name, address, or description.

    Args:
        query: Search query to find projects

    Returns:
        Matching projects
    """
    return await make_request("GET", "/search", params={"q": query, "type": "project"})


@mcp.tool()
async def get_project_details(projectId: str) -> Dict[str, Any]:
    """
    Get comprehensive project details including metadata and current status.

    Args:
        projectId: The GUID of the project

    Returns:
        Detailed project information
    """
    return await make_request("GET", "/project-details", params={"projectId": projectId})


@mcp.tool()
async def list_schedules(
    page: int = 1,
    limit: int = 5,
    projectId: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve project schedules, optionally filtered by project.

    Args:
        page: Page number (default: 1)
        limit: Items per page (default: 5)
        projectId: Optional project GUID to get schedules and tasks for that project

    Returns:
        Project schedules and optionally tasks if projectId is provided
    """
    params = {"page": page, "limit": limit}

    if projectId:
        # Fetch both schedules and tasks in parallel
        import asyncio
        schedules, tasks = await asyncio.gather(
            make_request("GET", "/project-schedules", params={"projectId": projectId}),
            make_request("GET", "/project-schedule-tasks", params={"projectId": projectId})
        )
        return {
            "schedules": schedules,
            "tasks": tasks
        }

    return await make_request("GET", "/project-schedules", params=params)


# ==========================================
# 4. ACTION ITEMS TOOLS
# ==========================================

@mcp.tool()
async def find_action_items(
    query: str,
    projectId: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for action items by title or description.

    Args:
        query: Search query to find action items
        projectId: Optional project GUID to filter action items by project

    Returns:
        Matching action items
    """
    params = {"q": query, "type": "action-item"}
    if projectId:
        params["projectId"] = projectId

    return await make_request("GET", "/search", params=params)


# ==========================================
# 5. FINANCIAL TOOLS
# ==========================================

@mcp.tool()
async def get_financials(projectId: str) -> Dict[str, Any]:
    """
    Get comprehensive financial data for a project including job balances and cost variance.

    Args:
        projectId: The GUID of the project to retrieve financial data for

    Returns:
        Combined financial data (job balances and cost variance)
    """
    import asyncio

    # Fetch both in parallel
    job_balances, cost_variance = await asyncio.gather(
        make_request("GET", "/job-balances", params={"projectId": projectId}),
        make_request("GET", "/cost-variance", params={"projectId": projectId})
    )

    return {
        "jobBalances": job_balances,
        "costVariance": cost_variance
    }


@mcp.tool()
async def get_transactions(
    projectId: str,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get transaction list for a project with optional date range filtering.

    Args:
        projectId: The GUID of the project to retrieve transactions for
        startDate: Start date in ISO-8601 format (e.g., 2024-01-01)
        endDate: End date in ISO-8601 format (e.g., 2024-12-31)

    Returns:
        List of transactions
    """
    params = {"projectId": projectId}
    if startDate:
        params["startDate"] = startDate
    if endDate:
        params["endDate"] = endDate

    return await make_request("GET", "/transactions", params=params)


# ==========================================
# 6. SEARCH TOOLS
# ==========================================

@mcp.tool()
async def search(
    query: str,
    type: Optional[str] = None,
    projectId: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generic search tool that can search across multiple entity types.

    Args:
        query: Search query
        type: Entity type to search (project, estimate, schedule, proposal,
              estimateCategory, constructionTask, action-item)
        projectId: Optional project GUID to filter results by project

    Returns:
        Search results matching the query
    """
    params = {"q": query}
    if type:
        params["type"] = type
    if projectId:
        params["projectId"] = projectId

    return await make_request("GET", "/search", params=params)


# ==========================================
# 7. ASYNC AGENT TOOL (Complex Workflows)
# ==========================================

@mcp.tool()
async def async_agent(prompt: str, ctx) -> Dict[str, Any]:
    """
    Delegate complex multi-step workflows to the async-agent system with real-time progress.

    Use this for tasks that require multiple coordinated steps, data gathering from
    multiple sources, or complex orchestration. Supports operations up to 10 minutes.

    Args:
        prompt: The task or question to send to the async-agent

    Returns:
        Result from the async-agent after processing the workflow
    """
    ASYNC_AGENT_URL = "https://joeapi-async-agent.fly.dev/webhooks/prompt-stream"
    TIMEOUT = 600  # 10 minutes (increased from 6 minutes)

    payload = {
        "prompt": prompt,
        "searchWorkflow": True,
        "async": False
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Make SSE streaming request
            async with client.stream(
                "POST",
                ASYNC_AGENT_URL,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()

                final_result = None
                progress_count = 0

                # Process SSE stream
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    try:
                        import json
                        event_data = json.loads(line[6:])  # Remove "data: " prefix

                        if event_data.get("type") == "progress":
                            progress_count += 1
                            progress_pct = event_data.get('progress', 0)
                            progress_msg = event_data.get('message', '')

                            # Log progress (visible in FastMCP Cloud logs)
                            print(f"[async] Progress {progress_count}: {progress_msg} ({progress_pct}%)")

                            # Report progress to keep connection alive and inform client
                            await ctx.report_progress(
                                progress=progress_pct,
                                total=100,
                                message=progress_msg
                            )

                        elif event_data.get("type") == "complete":
                            final_result = event_data.get("data")
                            print(f"[async] Completed with {progress_count} progress events")

                            # Report final completion
                            await ctx.report_progress(
                                progress=100,
                                total=100,
                                message="Workflow completed successfully"
                            )

                        elif event_data.get("type") == "error":
                            raise Exception(f"Async-agent error: {event_data.get('message')}")

                    except json.JSONDecodeError:
                        continue

                if not final_result:
                    raise Exception(f"Stream ended without completion (received {progress_count} progress events)")

                return final_result

        except httpx.TimeoutException:
            raise Exception(f"Async-agent timeout: Request exceeded {TIMEOUT} seconds")
        except httpx.HTTPStatusError as e:
            error_text = await e.response.aread()
            raise Exception(f"Async-agent error ({e.response.status_code}): {error_text.decode()}")


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    # Run with HTTP transport for FastMCP Cloud compatibility
    # Can also use stdio for local Claude Desktop integration
    mcp.run(transport="http", port=8000)
