import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_connection():
    command = "python"
    args = ["mcp_server.py"]
    server_params = StdioServerParameters(command=command, args=args)
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connection successful!")
                tools = await session.list_tools()
                print(f"Tools: {tools}")
    except Exception as e:
        print(f"Connection failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
