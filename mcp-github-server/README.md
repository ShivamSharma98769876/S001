# GitHub MCP Server

A Model Context Protocol (MCP) server for interacting with GitHub repositories. This server provides tools and resources for managing your GitHub repository programmatically.

## Repository

This server is configured for: **https://github.com/ShivamSharma98769876/S001/**

## Features

### Tools Available

1. **get_repository_info** - Get information about the repository
2. **list_files** - List files in the repository
3. **read_file** - Read file contents from the repository
4. **create_or_update_file** - Create or update files in the repository
5. **list_commits** - List recent commits
6. **get_commit** - Get details of a specific commit
7. **list_issues** - List issues in the repository
8. **create_issue** - Create a new issue
9. **list_pull_requests** - List pull requests
10. **get_branch_info** - Get information about a branch

### Resources Available

- `github://repository` - Repository information
- `github://commits` - Recent commits
- `github://issues` - Open issues

## Setup

### 1. Install Dependencies

```bash
cd mcp-github-server
npm install
```

### 2. Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name (e.g., "MCP Server")
4. Select scopes:
   - `repo` (Full control of private repositories)
5. Click "Generate token"
6. Copy the token

### 3. Configure Environment

Create a `.env` file in the `mcp-github-server` directory:

```bash
cp .env.example .env
```

Edit `.env` and add your token:

```
GITHUB_TOKEN=your_github_token_here
```

### 4. Build the Server

```bash
npm run build
```

### 5. Run the Server

```bash
npm start
```

Or for development:

```bash
npm run dev
```

## Usage with MCP Clients

### Cursor Configuration

Add this to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["/path/to/mcp-github-server/dist/index.js"],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "node",
      "args": ["/absolute/path/to/mcp-github-server/dist/index.js"],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

## Example Usage

Once connected, you can use the MCP server to:

- Read files from your repository
- Create or update files
- List commits and view commit history
- Manage issues
- View pull requests
- Get repository information

## Security Notes

- Never commit your `.env` file or GitHub token
- Keep your token secure and rotate it regularly
- Use environment variables for tokens in production
- The token needs `repo` scope to modify the repository

## Troubleshooting

### Token Issues

If you get authentication errors:
1. Verify your token is correct in `.env`
2. Check that the token has `repo` scope
3. Ensure the token hasn't expired

### Build Issues

If TypeScript compilation fails:
```bash
npm install --save-dev typescript @types/node
npm run build
```

## License

MIT

