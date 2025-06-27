"""
CRUD tools for Kintone MCP server.

This module provides tools for creating, updating, and deleting records in Kintone applications.
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


def get_crud_tools() -> List[types.Tool]:
    """Get list of CRUD tools."""
    return [
        types.Tool(
            name="kintone_create_record",
            description="Create a new record in a Kintone app with field validation. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    },
                    "record_data": {
                        "type": "object",
                        "description": "Record data as key-value pairs where keys are field codes and values are field values. Each field value should be an object with 'value' property."
                    }
                },
                "required": ["app_id", "record_data"]
            }
        ),
        types.Tool(
            name="kintone_update_record",
            description="Update an existing record in a Kintone app with revision control. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "The ID of the record to update"
                    },
                    "record_data": {
                        "type": "object",
                        "description": "Record data to update as key-value pairs where keys are field codes and values are field values. Each field value should be an object with 'value' property."
                    },
                    "revision": {
                        "type": "integer",
                        "description": "Record revision number for optimistic locking (optional but recommended)"
                    }
                },
                "required": ["app_id", "record_id", "record_data"]
            }
        ),
        types.Tool(
            name="kintone_delete_record",
            description="Delete a record from a Kintone app by ID with safety confirmation. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    },
                    "record_id": {
                        "type": "string",
                        "description": "The ID of the record to delete"
                    },
                    "revision": {
                        "type": "integer",
                        "description": "Record revision number for optimistic locking (optional but recommended)"
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation flag to prevent accidental deletions (must be true)",
                        "default": False
                    }
                },
                "required": ["app_id", "record_id", "confirm"]
            }
        )
    ]


async def handle_crud_tools(name: str, arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle CRUD tool calls."""
    try:
        if name == "kintone_create_record":
            return await _handle_create_record(arguments, client)
        elif name == "kintone_update_record":
            return await _handle_update_record(arguments, client)
        elif name == "kintone_delete_record":
            return await _handle_delete_record(arguments, client)
        else:
            return [types.TextContent(
                type="text",
                text=f"Error: Unknown CRUD tool '{name}'"
            )]
    except Exception as e:
        logger.error(f"Error in CRUD tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def _handle_create_record(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_create_record tool call."""
    app_id = arguments.get("app_id")
    record_data = arguments.get("record_data")

    if not app_id or not record_data:
        return [types.TextContent(
            type="text",
            text="Error: Both app_id and record_data are required"
        )]

    if not isinstance(record_data, dict):
        return [types.TextContent(
            type="text",
            text="Error: record_data must be a dictionary"
        )]

    result = client.create_record(app_id=app_id, record_data=record_data)

    if result.get("success"):
        record_id = result.get("id")
        revision = result.get("revision")

        response_text = f"Successfully created record in app {app_id}\n"
        response_text += f"Record ID: {record_id}\n"
        response_text += f"Revision: {revision}\n\n"
        response_text += f"Created data:\n{json.dumps(record_data, indent=2, ensure_ascii=False)}"

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error creating record in app {app_id}: {error_msg}"
        )]


async def _handle_update_record(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_update_record tool call."""
    app_id = arguments.get("app_id")
    record_id = arguments.get("record_id")
    record_data = arguments.get("record_data")
    revision = arguments.get("revision")

    if not app_id or not record_id or not record_data:
        return [types.TextContent(
            type="text",
            text="Error: app_id, record_id, and record_data are required"
        )]

    if not isinstance(record_data, dict):
        return [types.TextContent(
            type="text",
            text="Error: record_data must be a dictionary"
        )]

    result = client.update_record(
        app_id=app_id,
        record_id=record_id,
        record_data=record_data,
        revision=revision
    )

    if result.get("success"):
        new_revision = result.get("revision")

        response_text = f"Successfully updated record {record_id} in app {app_id}\n"
        response_text += f"New revision: {new_revision}\n\n"
        response_text += f"Updated data:\n{json.dumps(record_data, indent=2, ensure_ascii=False)}"

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error updating record {record_id} in app {app_id}: {error_msg}"
        )]


async def _handle_delete_record(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_delete_record tool call."""
    app_id = arguments.get("app_id")
    record_id = arguments.get("record_id")
    revision = arguments.get("revision")
    confirm = arguments.get("confirm", False)

    if not app_id or not record_id:
        return [types.TextContent(
            type="text",
            text="Error: Both app_id and record_id are required"
        )]

    if not confirm:
        return [types.TextContent(
            type="text",
            text="Error: Deletion not confirmed. Set 'confirm' parameter to true to proceed with deletion."
        )]

    result = client.delete_record(
        app_id=app_id,
        record_id=record_id,
        revision=revision
    )

    if result.get("success"):
        response_text = f"Successfully deleted record {record_id} from app {app_id}"
        if revision:
            response_text += f" (revision: {revision})"

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error deleting record {record_id} from app {app_id}: {error_msg}"
        )]