"""
Authentication module for MCP servers.

This module provides reusable authentication middleware for FastMCP servers,
supporting both JWT (Bearer) and API key authentication methods.
"""

from .middleware import install_auth

__all__ = ["install_auth"]
