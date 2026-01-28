# AI Workspace MCP Server

A Model Context Protocol (MCP) server that provides AI with a secure workspace for file management and Python script execution. Designed to run on Vercel as a serverless function.

## Features

### File Management Tools
- **create_file** - Create new files with content
- **read_file** - Read file contents
- **update_file** - Update existing files
- **delete_file** - Delete files
- **list_files** - List files and directories
- **create_directory** - Create new directories

### Code Execution
- **execute_python** - Execute Python scripts with arguments (30-second timeout)

## Setup on Vercel

### 1. Install Vercel CLI (Optional)
```bash
npm install -g vercel
```

### 2. Project Structure
Your project should look like this:
```
ai-workspace-mcp/
├── api/
│   └── mcp.py          # Serverless function
├── vercel.json         # Vercel configuration
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

### 3. Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your Git repository (or upload files)
4. Vercel will auto-detect Python and deploy

#### Option B: Deploy via CLI
```bash
# Login to Vercel
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

### 4. Get Your Deployment URL
After deployment, Vercel will give you a URL like:
`https://your-project-name.vercel.app`

## API Endpoints

Once deployed, your server will have these endpoints:

### GET /
Returns server information and status
```bash
curl https://your-project.vercel.app/
```

### GET /health
Health check endpoint
```bash
curl https://your-project.vercel.app/health
```

### GET /tools
List all available tools
```bash
curl https://your-project.vercel.app/tools
```

### POST /execute
Execute a tool
```bash
curl -X POST https://your-project.vercel.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_file",
    "arguments": {
      "filepath": "hello.py",
      "content": "print(\"Hello World!\")"
    }
  }'
```

## Using with AI Clients

### Claude Desktop Configuration

Add this to your Claude Desktop config:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ai-workspace": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "https://your-project.vercel.app/execute",
        "-H", "Content-Type: application/json",
        "-d", "@-"
      ]
    }
  }
}
```

### Using the API Directly

You can integrate this with any AI that supports HTTP tool calling:

```python
import requests

# Create a file
response = requests.post(
    "https://your-project.vercel.app/execute",
    json={
        "tool": "create_file",
        "arguments": {
            "filepath": "script.py",
            "content": "print('Hello from AI!')"
        }
    }
)
print(response.json())

# Execute the file
response = requests.post(
    "https://your-project.vercel.app/execute",
    json={
        "tool": "execute_python",
        "arguments": {
            "filepath": "script.py"
        }
    }
)
print(response.json())
```

## Security Features

- **Sandboxed Workspace**: All file operations are restricted to `/tmp/workspace`
- **Path Validation**: Prevents directory traversal attacks
- **Execution Timeout**: Python scripts are limited to 30 seconds
- **CORS Enabled**: Allows cross-origin requests
- **Serverless Isolation**: Each request runs in an isolated environment

## Tool Examples

### Create and Execute a Python Script

```bash
# Create a file
curl -X POST https://your-project.vercel.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_file",
    "arguments": {
      "filepath": "hello.py",
      "content": "print(\"Hello from Vercel!\")"
    }
  }'

# Execute it
curl -X POST https://your-project.vercel.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "execute_python",
    "arguments": {
      "filepath": "hello.py"
    }
  }'
```

### List Files

```bash
curl -X POST https://your-project.vercel.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_files",
    "arguments": {}
  }'
```

### Create Directory Structure

```bash
curl -X POST https://your-project.vercel.app/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_directory",
    "arguments": {
      "dirpath": "scripts"
    }
  }'
```

## Response Format

All tool executions return JSON:

**Success Response:**
```json
{
  "success": true,
  "message": "Successfully created file: hello.py\nSize: 26 bytes"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "File not found: nonexistent.py"
}
```

**Execute Python Response:**
```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "Hello from Vercel!\n",
  "stderr": ""
}
```

## Important Notes

### Vercel Limitations
- **Temporary Storage**: Files in `/tmp` are ephemeral and cleared between invocations
- **10-second timeout**: Vercel functions timeout after 10 seconds on free tier (25s on Pro)
- **Cold Starts**: First request may be slower due to cold start
- **No Persistent State**: Each function invocation starts fresh

### For Persistent Storage
If you need persistent file storage, consider:
1. Using Vercel KV, Postgres, or Blob storage
2. Integrating with AWS S3, Google Cloud Storage, etc.
3. Using a database to store file contents

## Environment Variables (Optional)

You can set environment variables in Vercel Dashboard:
- `WORKSPACE_PATH` - Custom workspace path (default: `/tmp/workspace`)
- `EXECUTION_TIMEOUT` - Python execution timeout in seconds (default: 30)

## Local Development

Test locally before deploying:

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Python's built-in server
cd api
python -m http.server 8000

# Or use Vercel CLI
vercel dev
```

Then test with:
```bash
curl http://localhost:8000/health
```

## Troubleshooting

### "Module not found" errors
Ensure `requirements.txt` is in the project root and contains all dependencies.

### Timeout errors
- Reduce Python script complexity
- Upgrade to Vercel Pro for longer timeouts
- Use async operations where possible

### File not persisting
Remember: `/tmp` storage is ephemeral on Vercel. Files won't persist between invocations.

## Advanced Usage

### Custom MCP Client

```python
class VercelMCPClient:
    def __init__(self, base_url):
        self.base_url = base_url
    
    def call_tool(self, tool_name, arguments):
        response = requests.post(
            f"{self.base_url}/execute",
            json={"tool": tool_name, "arguments": arguments}
        )
        return response.json()
    
    def list_tools(self):
        response = requests.get(f"{self.base_url}/tools")
        return response.json()

# Usage
client = VercelMCPClient("https://your-project.vercel.app")
result = client.call_tool("create_file", {
    "filepath": "test.py",
    "content": "print('test')"
})
```

## Contributing

Feel free to extend this server with additional tools:
1. Add tool definition to `get_tools()`
2. Implement handler in `execute_tool()`
3. Update documentation

## License

MIT License - modify and use as needed.

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Issues**: Open an issue or modify the code as needed