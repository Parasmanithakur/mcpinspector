import asyncio
from typing import Optional, List, Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
import logging

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, command: Optional[str] = None, args: List[str] = [], url: Optional[str] = None):
        self.command = command
        self.args = args
        self.url = url
        self.session: Optional[ClientSession] = None
        
        self._connection_task = None
        self._stop_event = asyncio.Event()

    async def _connection_manager(self, url: Optional[str], command: Optional[str], args: List[str], ready_event: asyncio.Event, error_queue: list):
        exit_stack = AsyncExitStack()
        try:
            if url:
                logger.info(f"Connecting to SSE in background task: {url}")
                read_stream, write_stream = await exit_stack.enter_async_context(sse_client(url))
                session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            elif command:
                logger.info(f"Connecting to STDIO in background task: {command} {' '.join(args)}")
                server_params = StdioServerParameters(command=command, args=args)
                read_stream, write_stream = await exit_stack.enter_async_context(stdio_client(server_params))
                session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            else:
                raise ValueError("Either command or url must be provided for connection")

            await session.initialize()
            logger.info("MCP session initialized successfully")
            
            self.session = session
            ready_event.set()
            
            # Keep the context alive until a stop is requested
            await self._stop_event.wait()
            logger.info("Background connection task stopping...")
            
        except asyncio.CancelledError:
            logger.info("Background connection task cancelled")
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}", exc_info=True)
            error_queue.append(e)
            ready_event.set()
        finally:
            self.session = None
            try:
                await exit_stack.aclose()
            except Exception as e:
                logger.warning(f"Error during context cleanup: {e}")

    async def connect(self, url: Optional[str] = None):
        """ESTABLISH connection to the MCP server securely using a dedicated background task."""
        
        if self._connection_task:
            await self.cleanup()
            
        new_url = url or self.url
        new_command = self.command if not url else None
        new_args = self.args if not url else []
        
        self.url = new_url
        self.command = new_command
        self.args = new_args
        
        ready_event = asyncio.Event()
        self._stop_event.clear()
        error_queue = []
        
        self._connection_task = asyncio.create_task(
            self._connection_manager(new_url, new_command, new_args, ready_event, error_queue)
        )
        
        # Wait for the background task to either succeed or fail initialization
        await ready_event.wait()
        
        if error_queue:
            err = error_queue[0]
            self._connection_task = None
            raise err
            
        return self.session

    async def list_tools(self):
        """List available tools from the server."""
        if not self.session:
            raise RuntimeError("Not connected to an MCP server")
        return await self.session.list_tools()

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a tool on the server."""
        if not self.session:
            raise RuntimeError("Not connected to an MCP server")
        return await self.session.call_tool(tool_name, arguments)

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up MCPClient resources...")
        if self._connection_task:
            self._stop_event.set()
            try:
                await asyncio.wait_for(self._connection_task, timeout=2.0)
            except asyncio.TimeoutError:
                self._connection_task.cancel()
            except Exception:
                pass
            self._connection_task = None
        self.session = None
