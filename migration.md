# TypeScript with Smithery CLI

> Migrate your TypeScript MCP servers to Streamable HTTP, with STDIO support for backwards compatibility

## When to Use This Approach

Choose TypeScript with Smithery CLI when you:

* Want the simplest migration path from STDIO to HTTP
* Are using the official MCP SDK and don't need custom middleware
* Want Smithery to handle containerization and deployment
* Want to maintain backward compatibility with STDIO transport
* Need a fully featured interactive development playground for testing

<Card title="Show me the repo" icon="github" href="https://github.com/smithery-ai/smithery-cookbook/tree/main/servers/typescript/migrate_stdio_to_http/server_with_smithery_cli">
  View the fully runnable GitHub repo for this example
</Card>

## What We're Building

We'll build a simple MCP server with a `count_characters` tool that:

* Takes text input and counts occurrences of a specific character
* Validates an API key from Smithery configuration to demonstrate configuration handling
* Uses Smithery CLI for building the server and containerization
* Supports both HTTP and STDIO transport

## Code Migration

### Let's say you start with this...

Here's a typical STDIO-based MCP server that you might be starting with:

```typescript  theme={null}
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Create STDIO server
const server = new McpServer({
  name: "Character Counter",
  version: "1.0.0"
});

// Get case sensitivity from environment variable
const caseSensitive = process.env.CASE_SENSITIVE === 'true';

// Register tool
server.registerTool("count_characters", {
  description: "Count occurrences of a specific character in text",
  inputSchema: {
    text: { type: "string", description: "The text to search in" },
    character: { type: "string", description: "The character to count" }
  }
}, async ({ text, character }) => {
  // Tool implementation with API key validation, etc.
  // ...
});

// Run with STDIO transport
const transport = new StdioServerTransport();
await server.server.connect(transport);
```

### Step 1: Update Imports and Configuration Schema

Now let's migrate this to work with Smithery CLI. First, update your imports and define your configuration schema:

```typescript  theme={null}
// src/index.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

// Define session configuration schema
export const configSchema = z.object({
  caseSensitive: z.boolean().optional().default(false).describe("Whether character matching should be case sensitive"),
});
```

<Note>
  **Configuration is Optional**: If your MCP server doesn't need any configuration (API keys, settings, etc.), you can remove all the config schema and validation code. The server will work perfectly fine without it.
</Note>

### Step 2: Create Server Function and Register Tools

Create the exported server function that Smithery CLI will use:

```typescript  theme={null}
// src/index.ts
export default function createServer({
  config,
}: {
  config: z.infer<typeof configSchema>;
}) {
  const server = new McpServer({
    name: "Character Counter",
    version: "1.0.0",
  });

  server.registerTool("count_characters", {
    title: "Count Characters",
    description: "Count occurrences of a specific character in text",
    inputSchema: {
      text: z.string().describe("The text to search in"),
      character: z.string().describe("The character to count (single character)"),
    },
  },
    async ({ text, character }) => {
      // Apply user preferences from config
      const searchText = config.caseSensitive ? text : text.toLowerCase();
      const searchChar = config.caseSensitive ? character : character.toLowerCase();
      
      // Count occurrences of the specific character
      const count = searchText.split(searchChar).length - 1;

      return {
        content: [
          { 
            type: "text", 
            text: `The character "${character}" appears ${count} times in the text.` 
          }
        ],
      };
    }
  );

  return server.server;
}
```

### Step 3: Maintaining STDIO Compatibility (Optional)

Now that we have our `createServer` function ready for Smithery CLI, we can optionally add STDIO support for backward compatibility. This gives you the best of both worlds:

* **HTTP deployment**: Smithery CLI uses your exported `createServer` function for scalable HTTP deployment
* **Local development**: Keep the familiar STDIO transport for backwards compatibility
* **NPM distribution**: Publish your server so others can install and run it locally

To enable STDIO support, add a `main()` function at the bottom of your file:

```typescript  theme={null}
// src/index.ts
async function main() {
  // Check if case sensitivity is enabled
  const caseSensitive = process.env.CASE_SENSITIVE === 'true';
  
  // Create server with configuration
  const server = createServer({
    config: {
      caseSensitive,
    },
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running in stdio mode");
}

// By default run the server with stdio transport
main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
```

<Note>
  **How it works**: When you deploy with Smithery CLI, it imports and uses your exported `createServer` function for HTTP transport. The `main()` function only runs when you execute the file directly (like `node dist/index.js`), giving you STDIO support for local development.
</Note>

## Configuration Changes

### Step 4: Update package.json

Configure `package.json` so Smithery CLI can find your exported server and add scripts for both HTTP and STDIO workflows:

```json  theme={null}
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "module": "src/index.ts", // [!code highlight]
  "scripts": {
    "dev": "smithery dev",
    "build": "npm run build:http",
    "build:stdio": "tsc",
    "build:http": "smithery build", // [!code highlight]
    "start": "npm run start:http",
    "start:http": "node .smithery/index.cjs",
    "start:stdio": "node dist/index.js",
    "prepublishOnly": "npm run build:stdio"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.18.2",
    "@smithery/sdk": "^1.6.4",
    "zod": "^3.25.46"
  },
  "devDependencies": {
    "@smithery/cli": "^1.4.0"
  }
}
```

**Important**: The `module` field tells Smithery CLI where to find your exported server function.

**Script explanations:**

* `dev`: Start development server with interactive playground
* `build`: Build for production (defaults to HTTP)
* `build:stdio`: Compile TypeScript for STDIO usage
* `build:http`: Build for Smithery HTTP deployment
* `start`: Start production server (defaults to HTTP)
* `start:http`: Run the Smithery-built HTTP server
* `start:stdio`: Run the compiled STDIO version locally
* `prepublishOnly`: Ensure STDIO build before publishing to npm

### Step 5: Update smithery.yaml

<CodeGroup>
  ```yaml Before (STDIO) theme={null}
  startCommand:
    type: stdio
    commandFunction: |
      (config) => ({
        command: 'npx',
        args: ['tsx', 'src/index.ts'],
        env: {
          CASE_SENSITIVE: config.caseSensitive
        }
      })
    configSchema:
      type: object
      properties:
        caseSensitive:
          type: boolean
          description: Whether character matching should be case sensitive
          default: false
    exampleConfig:
      caseSensitive: false
  ```

  ```yaml After (HTTP) theme={null}
  runtime: "typescript"
  ```
</CodeGroup>

That's it! The Smithery CLI handles the HTTP transport automatically.

<Note>
  **No Dockerfile needed**: Unlike custom container deployments, TypeScript projects using Smithery CLI don't require a Dockerfile. The CLI handles containerization automatically.
</Note>

<Tip>
  Install the CLI locally with:

  ```bash  theme={null}
  npm i -D @smithery/cli
  ```

  Add your SDK dependency explicitly:

  ```bash  theme={null}
  npm i @modelcontextprotocol/sdk @smithery/sdk
  ```
</Tip>

## Local Testing

1. **Using Smithery Interactive Playground:**

   ```bash  theme={null}
   # Start development server with interactive playground
   npm run dev
   ```

   The `npm run dev` command opens the **Smithery interactive playground** where you can:

   * Test your MCP server tools in real-time
   * See tool responses and debug issues
   * Validate your configuration schema
   * Experiment with different inputs

   <img src="https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=3c78c452c84004d16526e7db38804ee7" alt="Smithery Interactive Playground" className="rounded-lg shadow-sm" data-og-width="2834" width="2834" data-og-height="1550" height="1550" data-path="images/smithery_playground.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?w=280&fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=7211d8414733b79c937e055e0828948b 280w, https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?w=560&fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=9500535816ca56ddba79940f0ffd8aab 560w, https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?w=840&fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=e21c3731eb81e819130d20e4b944481b 840w, https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?w=1100&fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=ae91295d266f5d674ca99f4103fac2df 1100w, https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?w=1650&fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=2ebcd4ce7e6c94228bc2725b08d24c6a 1650w, https://mintcdn.com/smithery/VM0SEWDjb0U0Bzut/images/smithery_playground.png?w=2500&fit=max&auto=format&n=VM0SEWDjb0U0Bzut&q=85&s=4532e4de8d07ff12ad7f88ec78a92abd 2500w" />

2. **Building for Production:**

   ```bash  theme={null}
   # Build your server for deployment
   npm run build
   ```

   This compiles your TypeScript code and prepares it for deployment on Smithery.

3. **Testing STDIO mode locally:**
   ```bash  theme={null}
   # Build TypeScript code
   npm run build:stdio

   # Run in STDIO mode
   CASE_SENSITIVE=true npm run start:stdio
   ```

## Deployment

1. **Push Code**: Push your updated code (including updated `package.json` and `smithery.yaml`) to GitHub
2. **Deploy**: Go to [smithery.ai/new](https://smithery.ai/new) and connect your GitHub repository
3. **Verify**: Test your deployed server through the Smithery interface

The TypeScript runtime handles HTTP transport automatically - no additional configuration needed.

## Summary

This guide showed how to migrate a TypeScript MCP server from STDIO to HTTP transport using Smithery CLI. We transformed a traditional STDIO server into an exported `createServer` function using the official `McpServer` from the SDK, configured session handling with Zod, and updated `package.json` and `smithery.yaml` for automatic containerization. This approach provides the simplest migration path while supporting both HTTP deployment through Smithery CLI and optional STDIO backward compatibility.

***

**Need help?** Join our [Discord](https://discord.gg/Afd38S5p9A) or email [support@smithery.ai](mailto:support@smithery.ai) for assistance.

