#!/usr/bin/env node

/**
 * Local MCP Server Runner
 *
 * This is now just a simple wrapper that runs the main MCP server.
 * The main server (index.ts) already uses STDIO transport, so this
 * file simply re-exports and runs it.
 */

// Import and run the main server
import './index.js';

console.error('JoeAPI MCP Server running locally via local-server.ts');
