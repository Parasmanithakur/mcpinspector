import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent
import mcp.server.stdio

# Initialize the MCP Server
server = Server("sample-python-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_greeting",
            description="Returns a friendly greeting",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="add_numbers",
            description="Adds two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls."""
    if name == "get_greeting":
        user_name = arguments.get("name", "Stranger")
        return [TextContent(type="text", text=f"Hello, {user_name}! Welcome to the pure Python MCP world.")]
    
    elif name == "add_numbers":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        return [TextContent(type="text", text=f"The sum of {a} and {b} is {a + b}.")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sample-python-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
