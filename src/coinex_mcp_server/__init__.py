"""CoinEx MCP Server - A Model Context Protocol server for CoinEx cryptocurrency exchange.

This package enables AI agents to interact with the CoinEx exchange API through
the Model Context Protocol (MCP), supporting both spot and futures markets.
"""

__version__ = "0.1.0a6"
__author__ = "CoinEx MCP Contributors"
__license__ = "Apache-2.0"

from .coinex_client import CoinExClient

__all__ = ["CoinExClient", "__version__"]
