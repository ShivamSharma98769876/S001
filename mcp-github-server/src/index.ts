#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Octokit } from "@octokit/rest";
import * as dotenv from "dotenv";

dotenv.config();

// GitHub repository configuration
const GITHUB_OWNER = "ShivamSharma98769876";
const GITHUB_REPO = "S001";
const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";

// Initialize Octokit
const octokit = new Octokit({
  auth: GITHUB_TOKEN,
});

// Initialize MCP Server
const server = new Server(
  {
    name: "github-mcp-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
      resources: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_repository_info",
        description: "Get information about the GitHub repository",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "list_files",
        description: "List files in the repository",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to list files from (default: root)",
            },
          },
        },
      },
      {
        name: "read_file",
        description: "Read a file from the repository",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file to read",
              required: true,
            },
          },
          required: ["path"],
        },
      },
      {
        name: "create_or_update_file",
        description: "Create or update a file in the repository",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file",
              required: true,
            },
            content: {
              type: "string",
              description: "File content",
              required: true,
            },
            message: {
              type: "string",
              description: "Commit message",
              required: true,
            },
            branch: {
              type: "string",
              description: "Branch name (default: main)",
              default: "main",
            },
          },
          required: ["path", "content", "message"],
        },
      },
      {
        name: "list_commits",
        description: "List recent commits in the repository",
        inputSchema: {
          type: "object",
          properties: {
            limit: {
              type: "number",
              description: "Number of commits to return (default: 10)",
              default: 10,
            },
          },
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "get_repository_info": {
        const { data } = await octokit.repos.get({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
        });
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "list_files": {
        const path = (args as any)?.path || "";
        const { data } = await octokit.repos.getContent({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          path: path || "",
        });

        if (Array.isArray(data)) {
          const files = data.map((item: any) => ({
            name: item.name,
            path: item.path,
            type: item.type,
          }));
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(files, null, 2),
              },
            ],
          };
        }
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "read_file": {
        const path = (args as any)?.path;
        if (!path) {
          throw new Error("Path is required");
        }

        const { data } = await octokit.repos.getContent({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          path,
        });

        if ("content" in data && "encoding" in data) {
          const content =
            data.encoding === "base64"
              ? Buffer.from(data.content, "base64").toString("utf-8")
              : data.content;
          return {
            content: [
              {
                type: "text",
                text: content,
              },
            ],
          };
        }
        throw new Error("File content not available");
      }

      case "create_or_update_file": {
        const { path, content, message, branch } = args as any;
        
        let sha: string | undefined;
        try {
          const { data } = await octokit.repos.getContent({
            owner: GITHUB_OWNER,
            repo: GITHUB_REPO,
            path,
            ref: branch || "main",
          });
          if ("sha" in data) {
            sha = data.sha;
          }
        } catch (error: any) {
          if (error.status !== 404) {
            throw error;
          }
        }

        const encodedContent = Buffer.from(content).toString("base64");

        const { data } = await octokit.repos.createOrUpdateFileContents({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          path,
          message: message || `Update ${path}`,
          content: encodedContent,
          branch: branch || "main",
          sha,
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(data, null, 2),
            },
          ],
        };
      }

      case "list_commits": {
        const { limit = 10 } = args as any;
        const { data } = await octokit.repos.listCommits({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          per_page: limit,
        });

        const commits = data.map((commit) => ({
          sha: commit.sha,
          message: commit.commit.message,
          author: commit.commit.author?.name,
          date: commit.commit.author?.date,
        }));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(commits, null, 2),
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// List available resources
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "github://repository",
        name: "Repository Information",
        description: "Information about the GitHub repository",
        mimeType: "application/json",
      },
    ],
  };
});

// Handle resource requests
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  try {
    if (uri === "github://repository") {
      const { data } = await octokit.repos.get({
        owner: GITHUB_OWNER,
        repo: GITHUB_REPO,
      });
      return {
        contents: [
          {
            uri,
            mimeType: "application/json",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    }
    throw new Error(`Unknown resource: ${uri}`);
  } catch (error: any) {
    throw new Error(`Failed to read resource: ${error.message}`);
  }
});

// Start the server
async function main() {
  if (!GITHUB_TOKEN) {
    console.error("Error: GITHUB_TOKEN environment variable is not set");
    process.exit(1);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("GitHub MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});

