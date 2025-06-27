"""
Metadata tools for Kintone MCP server.

This module provides tools for exploring Kintone app structures, field definitions,
views, and form layouts.
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


def get_metadata_tools() -> List[types.Tool]:
    """Get list of metadata tools."""
    return [
        types.Tool(
            name="kintone_list_apps",
            description="🔍 START HERE: List available Kintone apps with pagination support. Use this first to get app IDs for other operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of apps to retrieve (default: 100, max: 100)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 100
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of apps to skip for pagination (default: 0)",
                        "default": 0,
                        "minimum": 0
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="kintone_get_app",
            description="Get detailed information about a single Kintone app. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    }
                },
                "required": ["app_id"]
            }
        ),
        types.Tool(
            name="kintone_get_form_fields",
            description="⭐ ESSENTIAL: Get field definitions, types, display names, and validation rules for a Kintone app. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    }
                },
                "required": ["app_id"]
            }
        ),
        types.Tool(
            name="kintone_get_views",
            description="Get app view configurations for a Kintone app. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    }
                },
                "required": ["app_id"]
            }
        ),
        types.Tool(
            name="kintone_get_form_layout",
            description="Get form layout information for a Kintone app. ⚠️ Use 'kintone_list_apps' first to get available app IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "app_id": {
                        "type": "string",
                        "description": "The ID of the Kintone app (use kintone_list_apps to see available app IDs)"
                    }
                },
                "required": ["app_id"]
            }
        )
    ]


async def handle_metadata_tools(name: str, arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle metadata tool calls."""
    try:
        if name == "kintone_list_apps":
            return await _handle_list_apps(arguments, client)
        elif name == "kintone_get_app":
            return await _handle_get_app(arguments, client)
        elif name == "kintone_get_form_fields":
            return await _handle_get_form_fields(arguments, client)
        elif name == "kintone_get_views":
            return await _handle_get_views(arguments, client)
        elif name == "kintone_get_form_layout":
            return await _handle_get_form_layout(arguments, client)
        else:
            return [types.TextContent(
                type="text",
                text=f"Error: Unknown metadata tool '{name}'"
            )]
    except Exception as e:
        logger.error(f"Error in metadata tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def _handle_list_apps(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_list_apps tool call."""
    limit = arguments.get("limit", 100)
    offset = arguments.get("offset", 0)

    # Validate limit
    if limit > 100:
        limit = 100
    elif limit < 1:
        limit = 1

    # Validate offset
    if offset < 0:
        offset = 0

    result = client.list_apps(limit=limit, offset=offset)

    if result.get("success"):
        apps = result.get("apps", [])

        response_text = f"Successfully retrieved {len(apps)} apps"
        if offset > 0:
            response_text += f" (Offset: {offset})"
        response_text += "\n\n"

        # Format apps list
        if apps:
            response_text += "Apps:\n"
            for app in apps:
                app_id = app.get("appId", "N/A")
                name = app.get("name", "N/A")
                description = app.get("description", "")
                created_at = app.get("createdAt", "N/A")

                response_text += f"- ID: {app_id}, Name: {name}"
                if description:
                    response_text += f", Description: {description}"
                response_text += f", Created: {created_at}\n"
        else:
            response_text += "No apps found."

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving apps: {error_msg}"
        )]


async def _handle_get_app(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_get_app tool call."""
    app_id = arguments.get("app_id")

    if not app_id:
        return [types.TextContent(
            type="text",
            text="Error: app_id is required"
        )]

    result = client.get_app(app_id=app_id)

    if result.get("success"):
        app = result.get("app", {})
        response_text = f"Successfully retrieved app information for app {app_id}\n\n"
        response_text += f"App Details:\n{json.dumps(app, indent=2, ensure_ascii=False)}"

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving app {app_id}: {error_msg}"
        )]


async def _handle_get_form_fields(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_get_form_fields tool call."""
    app_id = arguments.get("app_id")

    if not app_id:
        return [types.TextContent(
            type="text",
            text="Error: app_id is required"
        )]

    result = client.get_form_fields(app_id=app_id)

    if result.get("success"):
        properties = result.get("properties", {})

        response_text = f"Successfully retrieved form fields for app {app_id}\n\n"

        if properties:
            response_text += "Field Definitions:\n"
            for field_code, field_info in properties.items():
                field_type = field_info.get("type", "N/A")
                label = field_info.get("label", "N/A")
                required = field_info.get("required", False)

                response_text += f"- {field_code}: {label} ({field_type})"
                if required:
                    response_text += " [Required]"
                response_text += "\n"

            response_text += f"\nComplete Field Properties:\n{json.dumps(properties, indent=2, ensure_ascii=False)}"
        else:
            response_text += "No field definitions found."

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving form fields for app {app_id}: {error_msg}"
        )]


async def _handle_get_views(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_get_views tool call."""
    app_id = arguments.get("app_id")

    if not app_id:
        return [types.TextContent(
            type="text",
            text="Error: app_id is required"
        )]

    result = client.get_views(app_id=app_id)

    if result.get("success"):
        views = result.get("views", {})

        response_text = f"Successfully retrieved views for app {app_id}\n\n"

        if views:
            response_text += "Views:\n"
            for view_name, view_info in views.items():
                view_type = view_info.get("type", "N/A")
                view_id = view_info.get("id", "N/A")

                response_text += f"- {view_name}: {view_type} (ID: {view_id})\n"

            response_text += f"\nComplete View Configurations:\n{json.dumps(views, indent=2, ensure_ascii=False)}"
        else:
            response_text += "No views found."

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving views for app {app_id}: {error_msg}"
        )]


async def _handle_get_form_layout(arguments: Dict[str, Any], client: KintoneClient) -> List[types.TextContent]:
    """Handle kintone_get_form_layout tool call."""
    app_id = arguments.get("app_id")

    if not app_id:
        return [types.TextContent(
            type="text",
            text="Error: app_id is required"
        )]

    result = client.get_form_layout(app_id=app_id)

    if result.get("success"):
        layout = result.get("layout", [])

        response_text = f"Successfully retrieved form layout for app {app_id}\n\n"

        if layout:
            response_text += f"Form Layout ({len(layout)} sections):\n"
            for i, section in enumerate(layout, 1):
                section_type = section.get("type", "N/A")
                response_text += f"Section {i}: {section_type}\n"

            response_text += f"\nComplete Form Layout:\n{json.dumps(layout, indent=2, ensure_ascii=False)}"
        else:
            response_text += "No form layout found."

        return [types.TextContent(
            type="text",
            text=response_text
        )]
    else:
        error_msg = result.get("error", "Unknown error occurred")
        return [types.TextContent(
            type="text",
            text=f"Error retrieving form layout for app {app_id}: {error_msg}"
        )]