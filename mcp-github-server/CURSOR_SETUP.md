# How to Configure GitHub MCP Server in Cursor

## Step-by-Step Instructions

### 1. Open Cursor Settings

1. Open Cursor
2. Go to **File** → **Preferences** → **Settings** (or press `Ctrl+,`)
3. Search for **"MCP"** or **"Model Context Protocol"**
4. Click on **"MCP and Tools"** or **"MCP Servers"**

### 2. Add the MCP Server

In the MCP settings, you'll see a JSON configuration. Add your GitHub MCP server with a custom name:

```json
{
  "mcpServers": {
    "GitHub S001": {
      "command": "node",
      "args": [
        "C:/Users/SharmaS8/OneDrive - Unisys/Shivam Imp Documents-2024 June/PythonProgram/Strangle10Points/mcp-github-server/dist/index.js"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

### 3. Server Name Options

You can name your MCP server anything you want. Here are some suggestions:

- **"GitHub S001"** - Simple and descriptive
- **"GitHub Repository"** - Generic name
- **"S001 GitHub"** - Repository-focused
- **"My GitHub MCP"** - Personal identifier
- **"GitHub Strangle10Points"** - Project-specific

The name you choose will appear in Cursor's MCP server list.

### 4. Important Notes

1. **Path Format**: Use forward slashes (`/`) or escaped backslashes in the path
2. **Token Security**: Never commit your token to version control
3. **Build First**: Make sure to run `npm run build` before using the server
4. **Restart Cursor**: After adding the server, restart Cursor for changes to take effect

### 5. Verify Installation

After restarting Cursor:
1. The MCP server should appear in the MCP servers list
2. You should be able to use GitHub-related tools in your conversations
3. Check the Cursor logs if the server doesn't connect

### 6. Alternative: Using Relative Paths

If you prefer, you can use a relative path (though absolute paths are more reliable):

```json
{
  "mcpServers": {
    "GitHub S001": {
      "command": "node",
      "args": [
        "${workspaceFolder}/mcp-github-server/dist/index.js"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

## Troubleshooting

### Server Not Connecting

1. Check that the path is correct
2. Verify `npm run build` was successful
3. Check that `GITHUB_TOKEN` is set correctly
4. Look at Cursor's developer console for errors

### Token Issues

1. Generate a new token at: https://github.com/settings/tokens
2. Make sure it has `repo` scope
3. Update the token in the MCP configuration

## Example Configuration with Multiple Servers

If you have multiple MCP servers:

```json
{
  "mcpServers": {
    "GitHub S001": {
      "command": "node",
      "args": [
        "C:/Users/SharmaS8/OneDrive - Unisys/Shivam Imp Documents-2024 June/PythonProgram/Strangle10Points/mcp-github-server/dist/index.js"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    },
    "Another MCP Server": {
      "command": "python",
      "args": ["path/to/another/server.py"]
    }
  }
}
```

