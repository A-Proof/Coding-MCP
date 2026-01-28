#!/usr/bin/env python3
"""
SSE Endpoint for MCP - Vercel Serverless Function
This file creates the /api/sse endpoint automatically
"""

import json
import subprocess
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Workspace directory
WORKSPACE_DIR = Path("/tmp/workspace")
WORKSPACE_DIR.mkdir(exist_ok=True)


def get_safe_path(filepath: str) -> Path:
    """Ensure path is within workspace directory"""
    requested_path = WORKSPACE_DIR / filepath
    resolved_path = requested_path.resolve()
    
    if not str(resolved_path).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError("Path must be within workspace directory")
    
    return resolved_path


def get_tools() -> list[dict]:
    """Return list of available tools"""
    return [
        {
            "name": "create_file",
            "description": "Create a new file with content in the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file relative to workspace"},
                    "content": {"type": "string", "description": "Content to write to the file"},
                },
                "required": ["filepath", "content"],
            },
        },
        {
            "name": "read_file",
            "description": "Read the contents of a file from the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file relative to workspace"},
                },
                "required": ["filepath"],
            },
        },
        {
            "name": "update_file",
            "description": "Update an existing file's content in the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file relative to workspace"},
                    "content": {"type": "string", "description": "New content for the file"},
                },
                "required": ["filepath", "content"],
            },
        },
        {
            "name": "delete_file",
            "description": "Delete a file from the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file relative to workspace"},
                },
                "required": ["filepath"],
            },
        },
        {
            "name": "list_files",
            "description": "List all files in the workspace or a specific directory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path relative to workspace (empty for root)", "default": ""},
                },
            },
        },
        {
            "name": "execute_python",
            "description": "Execute a Python script from the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the Python script relative to workspace"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command line arguments", "default": []},
                },
                "required": ["filepath"],
            },
        },
        {
            "name": "create_directory",
            "description": "Create a new directory in the workspace",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dirpath": {"type": "string", "description": "Path to the directory relative to workspace"},
                },
                "required": ["dirpath"],
            },
        },
    ]


def execute_tool(name: str, arguments: dict) -> dict:
    """Execute a tool and return the result"""
    try:
        if name == "create_file":
            filepath = get_safe_path(arguments["filepath"])
            content = arguments["content"]
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding="utf-8")
            return {"success": True, "message": f"Created file: {arguments['filepath']} ({len(content)} bytes)"}
        
        elif name == "read_file":
            filepath = get_safe_path(arguments["filepath"])
            if not filepath.exists():
                return {"success": False, "error": f"File not found: {arguments['filepath']}"}
            content = filepath.read_text(encoding="utf-8")
            return {"success": True, "content": content, "filepath": arguments['filepath']}
        
        elif name == "update_file":
            filepath = get_safe_path(arguments["filepath"])
            content = arguments["content"]
            if not filepath.exists():
                return {"success": False, "error": f"File not found: {arguments['filepath']}"}
            filepath.write_text(content, encoding="utf-8")
            return {"success": True, "message": f"Updated file: {arguments['filepath']} ({len(content)} bytes)"}
        
        elif name == "delete_file":
            filepath = get_safe_path(arguments["filepath"])
            if not filepath.exists():
                return {"success": False, "error": f"File not found: {arguments['filepath']}"}
            filepath.unlink()
            return {"success": True, "message": f"Deleted file: {arguments['filepath']}"}
        
        elif name == "list_files":
            directory = arguments.get("directory", "")
            dirpath = get_safe_path(directory) if directory else WORKSPACE_DIR
            if not dirpath.exists():
                return {"success": False, "error": f"Directory not found: {directory}"}
            
            files = []
            dirs = []
            for item in sorted(dirpath.iterdir()):
                rel_path = str(item.relative_to(WORKSPACE_DIR))
                if item.is_file():
                    files.append({"name": rel_path, "size": item.stat().st_size, "type": "file"})
                else:
                    dirs.append({"name": rel_path, "type": "directory"})
            
            return {"success": True, "directories": dirs, "files": files}
        
        elif name == "execute_python":
            filepath = get_safe_path(arguments["filepath"])
            args = arguments.get("args", [])
            
            if not filepath.exists():
                return {"success": False, "error": f"Script not found: {arguments['filepath']}"}
            if filepath.suffix != ".py":
                return {"success": False, "error": "File must be a Python script (.py)"}
            
            try:
                result = subprocess.run(
                    [sys.executable, str(filepath)] + args,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(WORKSPACE_DIR),
                )
                return {
                    "success": True,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Script execution timed out after 30 seconds"}
            except Exception as e:
                return {"success": False, "error": f"Error executing script: {str(e)}"}
        
        elif name == "create_directory":
            dirpath = get_safe_path(arguments["dirpath"])
            dirpath.mkdir(parents=True, exist_ok=True)
            return {"success": True, "message": f"Created directory: {arguments['dirpath']}"}
        
        else:
            return {"success": False, "error": f"Unknown tool: {name}"}
    
    except ValueError as e:
        return {"success": False, "error": f"Security error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    """Vercel handler for SSE endpoint"""
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Accept, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET - initial SSE connection"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-transform')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()
        
        # MCP initialization message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "ai-workspace",
                    "version": "1.0.0"
                }
            }
        }
        
        sse_data = f"event: message\ndata: {json.dumps(init_message)}\n\n"
        self.wfile.write(sse_data.encode('utf-8'))
    
    def do_POST(self):
        """Handle POST - MCP messages"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-transform')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()
        
        try:
            message = json.loads(body) if body else {}
            method_name = message.get('method', '')
            msg_id = message.get('id', 1)
            
            # Handle different MCP methods
            if method_name == 'initialize':
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "ai-workspace", "version": "1.0.0"}
                    }
                }
            
            elif method_name == 'tools/list':
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": get_tools()}
                }
            
            elif method_name == 'tools/call':
                params = message.get('params', {})
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                result = execute_tool(tool_name, arguments)
                
                # Format result for MCP
                if result.get('success'):
                    content_text = result.get('message') or result.get('content') or json.dumps(result)
                else:
                    content_text = f"Error: {result.get('error', 'Unknown error')}"
                
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": content_text}]
                    }
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method_name}"
                    }
                }
            
            sse_data = f"event: message\ndata: {json.dumps(response)}\n\n"
            self.wfile.write(sse_data.encode('utf-8'))
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32603, "message": str(e)}
            }
            sse_data = f"event: message\ndata: {json.dumps(error_response)}\n\n"
            self.wfile.write(sse_data.encode('utf-8'))
