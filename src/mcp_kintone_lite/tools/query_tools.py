"""
Query tools for Kintone MCP server.

This module provides tools for querying and retrieving records from Kintone applications.
"""

import json
import logging
from typing import List, Dict, Any

import mcp.types as types

# Handle both direct execution and module imports
try:
    from ..client import KintoneClient
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from src.mcp_kintone_lite.client import KintoneClient

logger = logging.getLogger(__name__)


def get_query_tools() -> List[types.Tool]:
    """Get list of query tools."""
    return [
        types.Tool(
            name="kintone_get_records",
            description="Get multiple records from a Kintone app with query filtering, pagination, and field selection. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Query string for filtering records (optional). Use Kintone query syntax like 'status = \"Active\"'"
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of field codes to retrieve (optional). If not specified, all fields are returned"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to retrieve (default: 100, max: 500)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 500
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of records to skip for pagination (default: 0)",
                        "default": 0,
                        "minimum": 0
                    }
                },
                "required": ["app_id"]
            }
        ),
        types.Tool(
            name="kintone_get_record",
            description="Get a single record from a Kintone app by record ID. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "The ID of the record to retrieve"
                    }
                },
                "required": ["app_id", "record_id"]
            }
        )
    ]


async def handle_query_tools(name: str, arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle query tool calls."""
    try:
        if name == "kintone_get_records":
            return await _handle_get_records(arguments, client)
        elif name == "kintone_get_record":
            return await _handle_get_record(arguments, client)
        else:
            return [types.TextContent(
                type="text",
                text=f"Error: Unknown query tool '{name}'"
            )]
    except Exception as e:
        logger.error(f"Error in query tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def _handle_get_records(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_get_records tool call."""
    app_id = arguments.get("app_id")
    query = arguments.get("query")
    fields = arguments.get("fields")
    limit = arguments.get("limit", 100)
    offset = arguments.get("offset", 0)

    if not app_id:
        return [types.TextContent(
            type="text",
            text="Error: app_id is required"
        )]

    # Validate limit
    if limit > 500:
        limit = 500
    elif limit < 1:
        limit = 1

    # Validate offset
    if offset < 0:
        offset = 0

    result = client.get_records(
        app_id=app_id,
        query=query,
        fields=fields,
        limit=limit,
        offset=offset
    )

    if result.get("success"):
        total_count = result.get("totalCount", 0)
        records = result.get("records", [])

        response_text = f"Successfully retrieved {len(records)} records from app {app_id}"
        if total_count is not None:
            response_text += f" (Total: {total_count} records)"
        if offset > 0:
            response_text += f" (Offset: {offset})"
        if query:
            response_text += f" with query: {query}"

        response_text += f"\n\nRecords:\n{json.dumps(records, indent=2, ensure_ascii=False)}"

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving records from app {app_id}: {error_msg}"
        )]


async def _handle_get_record(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_get_record tool call."""
    app_id = arguments.get("app_id")
    record_id = arguments.get("record_id")

    if not app_id or not record_id:
        return [types.TextContent(
            type="text",
            text="Error: Both app_id and record_id are required"
        )]

    result = client.get_record(app_id=app_id, record_id=record_id)

    if result.get("success"):
        record = result.get("record", {})
        response_text = f"Successfully retrieved record {record_id} from app {app_id}\n\n"
        response_text += f"Record:\n{json.dumps(record, indent=2, ensure_ascii=False)}"

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving record {record_id} from app {app_id}: {error_msg}"
        )]