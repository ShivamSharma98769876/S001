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
            recursive: {
              type: "boolean",
              description: "Whether to list files recursively",
              default: false,
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
              description: "File content (base64 encoded or plain text)",
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
            branch: {
              type: "string",
              description: "Branch name (default: main)",
              default: "main",
            },
          },
        },
      },
      {
        name: "get_commit",
        description: "Get details of a specific commit",
        inputSchema: {
          type: "object",
          properties: {
            sha: {
              type: "string",
              description: "Commit SHA",
              required: true,
            },
          },
          required: ["sha"],
        },
      },
      {
        name: "list_issues",
        description: "List issues in the repository",
        inputSchema: {
          type: "object",
          properties: {
            state: {
              type: "string",
              description: "Issue state: open, closed, or all (default: open)",
              enum: ["open", "closed", "all"],
              default: "open",
            },
            limit: {
              type: "number",
              description: "Number of issues to return (default: 10)",
              default: 10,
            },
          },
        },
      },
      {
        name: "create_issue",
        description: "Create a new issue",
        inputSchema: {
          type: "object",
          properties: {
            title: {
              type: "string",
              description: "Issue title",
              required: true,
            },
            body: {
              type: "string",
              description: "Issue body/description",
            },
            labels: {
              type: "array",
              items: { type: "string" },
              description: "Labels to add to the issue",
            },
          },
          required: ["title"],
        },
      },
      {
        name: "list_pull_requests",
        description: "List pull requests in the repository",
        inputSchema: {
          type: "object",
          properties: {
            state: {
              type: "string",
              description: "PR state: open, closed, or all (default: open)",
              enum: ["open", "closed", "all"],
              default: "open",
            },
            limit: {
              type: "number",
              description: "Number of PRs to return (default: 10)",
              default: 10,
            },
          },
        },
      },
      {
        name: "get_branch_info",
        description: "Get information about a branch",
        inputSchema: {
          type: "object",
          properties: {
            branch: {
              type: "string",
              description: "Branch name (default: main)",
              default: "main",
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
            size: item.size,
            sha: item.sha,
          }));
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(files, null, 2),
              },
            ],
          };
        } else {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(data, null, 2),
              },
            ],
          };
        }
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
        } else {
          throw new Error("File content not available");
        }
      }

      case "create_or_update_file": {
        const { path, content, message, branch } = args as any;
        
        // Get current file SHA if it exists
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
          // File doesn't exist, that's okay
          if (error.status !== 404) {
            throw error;
          }
        }

        // Encode content to base64
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
        const { limit = 10, branch = "main" } = args as any;
        const { data } = await octokit.repos.listCommits({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          sha: branch,
          per_page: limit,
        });

        const commits = data.map((commit) => ({
          sha: commit.sha,
          message: commit.commit.message,
          author: commit.commit.author?.name,
          date: commit.commit.author?.date,
          url: commit.html_url,
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

      case "get_commit": {
        const { sha } = args as any;
        const { data } = await octokit.repos.getCommit({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          ref: sha,
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  sha: data.sha,
                  message: data.commit.message,
                  author: data.commit.author?.name,
                  date: data.commit.author?.date,
                  files: data.files?.map((f) => ({
                    filename: f.filename,
                    status: f.status,
                    additions: f.additions,
                    deletions: f.deletions,
                  })),
                  stats: data.stats,
                  url: data.html_url,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "list_issues": {
        const { state = "open", limit = 10 } = args as any;
        const { data } = await octokit.issues.listForRepo({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          state: state as "open" | "closed" | "all",
          per_page: limit,
        });

        const issues = data.map((issue) => ({
          number: issue.number,
          title: issue.title,
          state: issue.state,
          body: issue.body,
          labels: issue.labels.map((l: any) => l.name),
          created_at: issue.created_at,
          updated_at: issue.updated_at,
          url: issue.html_url,
        }));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(issues, null, 2),
            },
          ],
        };
      }

      case "create_issue": {
        const { title, body, labels } = args as any;
        const { data } = await octokit.issues.create({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          title,
          body: body || "",
          labels: labels || [],
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  number: data.number,
                  title: data.title,
                  state: data.state,
                  url: data.html_url,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "list_pull_requests": {
        const { state = "open", limit = 10 } = args as any;
        const { data } = await octokit.pulls.list({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          state: state as "open" | "closed" | "all",
          per_page: limit,
        });

        const prs = data.map((pr) => ({
          number: pr.number,
          title: pr.title,
          state: pr.state,
          body: pr.body,
          head: pr.head.ref,
          base: pr.base.ref,
          created_at: pr.created_at,
          updated_at: pr.updated_at,
          url: pr.html_url,
        }));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(prs, null, 2),
            },
          ],
        };
      }

      case "get_branch_info": {
        const { branch = "main" } = args as any;
        const { data } = await octokit.repos.getBranch({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          branch,
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  name: data.name,
                  sha: data.commit.sha,
                  message: data.commit.commit.message,
                  author: data.commit.commit.author?.name,
                  date: data.commit.commit.author?.date,
                  protected: data.protected,
                },
                null,
                2
              ),
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
      {
        uri: "github://commits",
        name: "Recent Commits",
        description: "List of recent commits",
        mimeType: "application/json",
      },
      {
        uri: "github://issues",
        name: "Open Issues",
        description: "List of open issues",
        mimeType: "application/json",
      },
    ],
  };
});

// Handle resource requests
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;

  try {
    switch (uri) {
      case "github://repository": {
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

      case "github://commits": {
        const { data } = await octokit.repos.listCommits({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          per_page: 10,
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

      case "github://issues": {
        const { data } = await octokit.issues.listForRepo({
          owner: GITHUB_OWNER,
          repo: GITHUB_REPO,
          state: "open",
          per_page: 10,
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

      default:
        throw new Error(`Unknown resource: ${uri}`);
    }
  } catch (error: any) {
    throw new Error(`Failed to read resource: ${error.message}`);
  }
});

// Start the server
async function main() {
  if (!GITHUB_TOKEN) {
    console.error("Error: GITHUB_TOKEN environment variable is not set");
    console.error("Please set it in a .env file or as an environment variable");
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

