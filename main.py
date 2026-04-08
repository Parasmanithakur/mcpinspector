import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Body, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from mcp_client import MCPClient
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Note: Default command/args are still defined but NOT automatically connected on startup.
MCP_SERVER_COMMAND = os.getenv("MCP_SERVER_COMMAND", sys.executable)
mcp_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "mcp_server.py"))
MCP_SERVER_ARGS = os.getenv("MCP_SERVER_ARGS", mcp_server_path).split()
if "-u" not in MCP_SERVER_ARGS:
    MCP_SERVER_ARGS.insert(0, "-u")

# Session management: route each browser tab to its own sandbox
active_sessions: Dict[str, MCPClient] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("MCP Inspector Backend starting in Multi-Tenant Dynamic Connection Mode")
    yield
    # Shutdown: Cleanup all sessions
    for session_id, client in active_sessions.items():
        try:
            await client.cleanup()
        except:
            pass
    active_sessions.clear()

app = FastAPI(title="MCP Inspector Backend", lifespan=lifespan)

# Enable CORS for the React UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ConnectRequest(BaseModel):
    url: Optional[str] = None
    command: Optional[str] = None
    args: List[str] = []

@app.get("/")
async def root():
    return {
        "message": "MCP Inspector Backend is running in Multi-Tenant Dynamic Connection Mode",
        "active_sessions_count": len(active_sessions)
    }

@app.post("/connect")
async def connect_server(request: ConnectRequest, x_session_id: str = Header(default=None)):
    """Endpoint to connect to a new MCP server dynamically for a specific session."""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID header is required")

    try:
        # Cleanup existing session if it exists to allow reconnecting
        if x_session_id in active_sessions:
            logger.info(f"Cleaning up old connection for session: {x_session_id}")
            await active_sessions[x_session_id].cleanup()
            
        # Spawn a brand new MCPClient specifically for this user
        client = MCPClient(MCP_SERVER_COMMAND, MCP_SERVER_ARGS)

        if request.url:
            await client.connect(url=request.url)
        elif request.command:
            client.command = request.command
            client.args = request.args
            await client.connect()
        else:
            await client.connect()
        
        # Register the client to the global session store
        active_sessions[x_session_id] = client
        server_info = request.url or f"{client.command} {' '.join(client.args)}"
        logger.info(f"Session {x_session_id} successfully connected to: {server_info}")
        return {"status": "connected", "server": server_info, "session_id": x_session_id}
    except Exception as e:
        error_msg = str(e) or "Failed to connect to the specified MCP server"
        logger.error(f"Connect error for session {x_session_id}: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/tools")
async def get_tools(x_session_id: str = Header(default=None)):
    """Endpoint to list tools from the MCP server for a specific session."""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID header is required")
        
    client = active_sessions.get(x_session_id)
    if not client or not client.session:
         raise HTTPException(status_code=400, detail="Not connected to any MCP server. Please connect first.")

    try:
        tools_result = await client.list_tools()
        return {"tools": [tool.model_dump() for tool in tools_result.tools]}
    except Exception as e:
        error_msg = str(e) or "An error occurred while listing tools"
        logger.error(f"Error listing tools for session {x_session_id}: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/call")
async def call_tool(request: ToolCallRequest, x_session_id: str = Header(default=None)):
    """Endpoint to execute a tool for a specific session."""
    if not x_session_id:
        raise HTTPException(status_code=400, detail="X-Session-ID header is required")
        
    client = active_sessions.get(x_session_id)
    if not client or not client.session:
        raise HTTPException(status_code=400, detail="Not connected to any MCP server")

    try:
        result = await client.call_tool(request.name, request.arguments)
        return {"result": result.model_dump()}
    except Exception as e:
        error_msg = str(e) or "An error occurred while calling the tool"
        logger.error(f"Error calling tool for session {x_session_id}: {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
