#!/usr/bin/env python3
"""
Example client for the Vercel MCP Server
Demonstrates how to interact with the API
"""

import requests
import json

# Update this with your Vercel deployment URL
BASE_URL = "https://your-project.vercel.app"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def list_tools():
    """List available tools"""
    print("Listing available tools...")
    response = requests.get(f"{BASE_URL}/tools")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def create_file_example():
    """Create a file"""
    print("Creating a Python file...")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "create_file",
            "arguments": {
                "filepath": "hello.py",
                "content": 'print("Hello from Vercel MCP!")\nprint("AI Workspace is operational")'
            }
        }
    )
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def execute_python_example():
    """Execute a Python script"""
    print("Executing Python script...")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "execute_python",
            "arguments": {
                "filepath": "hello.py"
            }
        }
    )
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Exit Code: {result.get('exit_code')}")
    print(f"Output:\n{result.get('stdout')}")
    if result.get('stderr'):
        print(f"Errors:\n{result.get('stderr')}")
    print()


def list_files_example():
    """List files in workspace"""
    print("Listing files...")
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "list_files",
            "arguments": {}
        }
    )
    result = response.json()
    if result.get('success'):
        print(f"Files: {json.dumps(result.get('files'), indent=2)}")
        print(f"Directories: {json.dumps(result.get('directories'), indent=2)}\n")


def create_data_pipeline():
    """Create and run a data processing pipeline"""
    print("Creating data processing pipeline...")
    
    # Create directory
    requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "create_directory",
            "arguments": {"dirpath": "data"}
        }
    )
    
    # Create input data
    requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "create_file",
            "arguments": {
                "filepath": "data/input.json",
                "content": json.dumps([1, 2, 3, 4, 5])
            }
        }
    )
    
    # Create processing script
    script_content = """
import json

with open('data/input.json', 'r') as f:
    data = json.load(f)

result = sum(data)
print(f"Sum of {data} = {result}")

with open('data/output.json', 'w') as f:
    json.dump({"sum": result}, f)
"""
    
    requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "create_file",
            "arguments": {
                "filepath": "process.py",
                "content": script_content
            }
        }
    )
    
    # Execute script
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "execute_python",
            "arguments": {"filepath": "process.py"}
        }
    )
    
    result = response.json()
    print(f"Processing output:\n{result.get('stdout')}")
    
    # Read result
    response = requests.post(
        f"{BASE_URL}/execute",
        json={
            "tool": "read_file",
            "arguments": {"filepath": "data/output.json"}
        }
    )
    
    result = response.json()
    if result.get('success'):
        print(f"Result file content: {result.get('content')}\n")


def main():
    """Run all examples"""
    print("=" * 60)
    print("Vercel MCP Server - Example Client")
    print("=" * 60)
    print()
    
    try:
        test_health()
        list_tools()
        create_file_example()
        execute_python_example()
        list_files_example()
        create_data_pipeline()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
    
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("\nMake sure to update BASE_URL with your Vercel deployment URL")


if __name__ == "__main__":
    main()