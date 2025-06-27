"""
Kintone API client wrapper for MCP server.

This module provides a simplified interface to interact with Kintone REST API,
handling authentication, connection validation, and common operations.
"""

import os
import logging
import requests
import json
from typing import Dict, List, Any, Optional
import base64
from urllib.parse import urljoin


logger = logging.getLogger(__name__)


class KintoneError(Exception):
    """Custom exception for Kintone API errors."""
    pass


class KintoneClient:
    """Kintone client wrapper with Basic Authentication."""

    def __init__(self):
        self.subdomain = os.getenv('KINTONE_SUBDOMAIN')
        self.username = os.getenv('KINTONE_USERNAME')
        self.password = os.getenv('KINTONE_PASSWORD')

        if not self.subdomain:
            raise KintoneError("KINTONE_SUBDOMAIN environment variable is required")
        if not self.username:
            raise KintoneError("KINTONE_USERNAME environment variable is required")
        if not self.password:
            raise KintoneError("KINTONE_PASSWORD environment variable is required")

        self.base_url = f"https://{self.subdomain}.cybozu.com/k/v1/"
        self.session = None
        self._connect()

    def _connect(self) -> None:
        """Initialize the session with Basic Authentication."""
        try:
            self.session = requests.Session()

            # Create Basic Authentication header
            credentials = f"{self.username}:{self.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            # Set authentication headers
            self.session.headers.update({
                'X-Cybozu-Authorization': encoded_credentials,
                'User-Agent': 'mcp-kintone-lite/1.0'
            })

            logger.info(f"Connected to Kintone at {self.base_url}")

        except Exception as e:
            logger.error(f"Failed to connect to Kintone: {e}")
            raise KintoneError(f"Connection failed: {e}")

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None,
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Kintone API."""
        if not self.session:
            raise KintoneError("Not connected to Kintone")

        url = f"{self.base_url}{endpoint}"

        try:
            # Add Content-Type header for POST, PUT, DELETE requests
            headers = {}
            if method in ['POST', 'PUT', 'DELETE']:
                headers['Content-Type'] = 'application/json'

            if method == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, json=data, headers=headers)
            else:
                raise KintoneError(f"Unsupported HTTP method: {method}")

            # Check for HTTP errors
            if response.status_code >= 400:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'HTTP {response.status_code} error')
                except:
                    error_message = f'HTTP {response.status_code} error'

                return {
                    "success": False,
                    "error": error_message,
                    "error_type": "HTTPError",
                    "status_code": response.status_code
                }

            # Parse JSON response
            try:
                result = response.json()
                return {
                    "success": True,
                    "data": result
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {e}",
                    "error_type": "JSONDecodeError"
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "RequestError"
            }

    # Query Tools
    def get_records(self, app_id: str, query: Optional[str] = None,
                   fields: Optional[List[str]] = None, limit: int = 100,
                   offset: int = 0) -> Dict[str, Any]:
        """Get multiple records with optional query filtering."""
        params = {
            'app': app_id
        }

        if query:
            params['query'] = query
        if fields:
            params['fields'] = fields
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset

        result = self._make_request('GET', 'records.json', params=params)

        if result['success']:
            return {
                "success": True,
                "records": result['data'].get('records', []),
                "totalCount": result['data'].get('totalCount', 0)
            }
        return result

    def get_record(self, app_id: str, record_id: str) -> Dict[str, Any]:
        """Get single record by ID."""
        params = {
            'app': app_id,
            'id': record_id
        }

        result = self._make_request('GET', 'record.json', params=params)

        if result['success']:
            return {
                "success": True,
                "record": result['data'].get('record', {})
            }
        return result

    # CRUD Tools
    def create_record(self, app_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create single record with field validation."""
        data = {
            'app': app_id,
            'record': record_data
        }

        result = self._make_request('POST', 'record.json', data=data)

        if result['success']:
            return {
                "success": True,
                "id": result['data'].get('id'),
                "revision": result['data'].get('revision')
            }
        return result

    def update_record(self, app_id: str, record_id: str, record_data: Dict[str, Any],
                     revision: Optional[int] = None) -> Dict[str, Any]:
        """Update single record with revision control."""
        data = {
            'app': app_id,
            'id': record_id,
            'record': record_data
        }

        if revision is not None:
            data['revision'] = revision

        result = self._make_request('PUT', 'record.json', data=data)

        if result['success']:
            return {
                "success": True,
                "revision": result['data'].get('revision')
            }
        return result

    def delete_record(self, app_id: str, record_id: str, revision: Optional[int] = None) -> Dict[str, Any]:
        """Delete record by ID."""
        data = {
            'app': app_id,
            'ids': [record_id]
        }

        if revision is not None:
            data['revisions'] = [revision]

        result = self._make_request('DELETE', 'records.json', data=data)

        if result['success']:
            return {
                "success": True,
                "deleted": True
            }
        return result

    # Metadata Tools
    def list_apps(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List available apps."""
        params = {}
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset

        result = self._make_request('GET', 'apps.json', params=params)

        if result['success']:
            return {
                "success": True,
                "apps": result['data'].get('apps', [])
            }
        return result

    def get_app(self, app_id: str) -> Dict[str, Any]:
        """Get single app information."""
        params = {'id': app_id}

        result = self._make_request('GET', 'app.json', params=params)

        if result['success']:
            return {
                "success": True,
                "app": result['data']
            }
        return result

    def get_form_fields(self, app_id: str) -> Dict[str, Any]:
        """Get field definitions, types, display names, validation rules."""
        params = {'app': app_id}

        result = self._make_request('GET', 'app/form/fields.json', params=params)

        if result['success']:
            return {
                "success": True,
                "properties": result['data'].get('properties', {})
            }
        return result

    def get_views(self, app_id: str) -> Dict[str, Any]:
        """Get app view configurations."""
        params = {'app': app_id}

        result = self._make_request('GET', 'app/views.json', params=params)

        if result['success']:
            return {
                "success": True,
                "views": result['data'].get('views', {})
            }
        return result

    def get_form_layout(self, app_id: str) -> Dict[str, Any]:
        """Get form layout information."""
        params = {'app': app_id}

        result = self._make_request('GET', 'app/form/layout.json', params=params)

        if result['success']:
            return {
                "success": True,
                "layout": result['data'].get('layout', [])
            }
        return result

    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        try:
            return {
                "success": True,
                "subdomain": self.subdomain,
                "base_url": self.base_url,
                "connected": self.session is not None
            }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "ConnectionError"
            }
