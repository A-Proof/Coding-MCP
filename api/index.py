#!/usr/bin/env python3
"""
Main API handler - This will be accessible at /api/index
"""

from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "MCP Server is running",
            "endpoints": {
                "sse": "/api/sse (for ChatGPT Apps)",
                "health": "/api/health"
            }
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
