#!/usr/bin/env python3
"""Simple Kintone MCP Server."""

import asyncio
import logging
import sys
import os
from typing import Dict, List, Any, Optional

from dotenv import load_dotenv

import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

# Handle both direct execution and module imports
try:
    from .client import KintoneClient
    from .tools import (
        get_query_tools, handle_query_tools,
        get_crud_tools, handle_crud_tools,
        get_metadata_tools, handle_metadata_tools
    )
except ImportError:
    # Add the src directory to the path for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.mcp_kintone_lite.client import KintoneClient
    from src.mcp_kintone_lite.tools import (
        get_query_tools, handle_query_tools,
        get_crud_tools, handle_crud_tools,
        get_metadata_tools, handle_metadata_tools
    )

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create server instance
server = Server("kintone-lite")

# Global client instance
kintone_client: Optional[KintoneClient] = None


def get_client() -> KintoneClient:
    """Get or create Kintone client instance."""
    global kintone_client
    if kintone_client is None:
        kintone_client = KintoneClient()
    return kintone_client


# TOOLS - Functions that AI can call

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    tools = []
    tools.extend(get_query_tools())
    tools.extend(get_crud_tools())
    tools.extend(get_metadata_tools())
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls by routing to appropriate tool modules."""
    client = get_client()

    # Query tools
    if name in ["kintone_get_records", "kintone_get_record"]:
        return await handle_query_tools(name, arguments, client)

    # CRUD tools
    elif name in ["kintone_create_record", "kintone_update_record", "kintone_delete_record"]:
        return await handle_crud_tools(name, arguments, client)

    # Metadata tools
    elif name in ["kintone_list_apps", "kintone_get_app", "kintone_get_form_fields",
                  "kintone_get_views", "kintone_get_form_layout"]:
        return await handle_metadata_tools(name, arguments, client)

    else:
        logger.error(f"Unknown tool: {name}")
        return [types.TextContent(
            type="text",
            text=f"Error: Unknown tool '{name}'"
        )]


async def run():
    """Main entry point for the MCP server."""
    logger.info("Starting Kintone MCP Server...")

    # Test connection on startup
    try:
        client = get_client()
        logger.info("Kintone connection established successfully")
    except Exception as e:
        logger.error(f"Failed to establish Kintone connection: {e}")
        logger.error("Please check your environment variables and Kintone configuration")
        return

    # Run the MCP server
    async with mcp.server.stdio.stdio_server() as (read, write):
        await server.run(
            read,
            write,
            InitializationOptions(
                server_name="kintone-lite",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    """Main entry point."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
