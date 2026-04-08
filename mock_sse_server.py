import asyncio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = Server("mock-sse-server")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="sse_echo",
            description="Echo through SSE",
            inputSchema={"type": "object", "properties": {"msg": {"type": "string"}}}
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    if name == "sse_echo":
        return [TextContent(type="text", text=f"SSE Echo: {arguments.get('msg', '')}")]
    return []

sse = SseServerTransport("/messages")

async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    path = scope["path"]
    method = scope["method"]

    if path == "/sse" and method == "GET":
        logger.info("New SSE connection resolving")
        try:
            async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mock-sse-server",
                        server_version="0.1.0",
                        capabilities=server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        except Exception as e:
            logger.error(f"SSE connection error: {e}", exc_info=True)

    elif path == "/messages" and method == "POST":
        logger.info("Handling POST message")
        await sse.handle_post_message(scope, receive, send)
        
    else:
        await send({
            "type": "http.response.start",
            "status": 404,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({
            "type": "http.response.body",
            "body": b"Not Found",
        })

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
