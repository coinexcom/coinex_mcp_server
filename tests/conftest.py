"""
Pytest configuration and fixtures for CoinEx MCP Server tests
"""
import os
import pytest
import asyncio
from typing import Generator
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from coinex_client import CoinExClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def public_client() -> CoinExClient:
    """Create a CoinEx client for public API testing (no authentication required)."""
    return CoinExClient(enable_env_credentials=False)


@pytest.fixture(scope="session") 
def auth_client() -> CoinExClient:
    """Create a CoinEx client with authentication (requires API credentials)."""
    return CoinExClient(enable_env_credentials=True)


@pytest.fixture(scope="session")
def has_auth_credentials() -> bool:
    """Check if authentication credentials are available."""
    return bool(os.getenv('COINEX_ACCESS_ID') and os.getenv('COINEX_SECRET_KEY'))


@pytest.fixture(params=[
    ("BTC", "USDT"),
    ("ETH", "USDT"),
    ("LTC", "USDT"),
])
def currency_pair(request):
    """Parametrized fixture for common currency pairs."""
    return request.param


@pytest.fixture(params=[
    CoinExClient.MarketType.SPOT,
    CoinExClient.MarketType.FUTURES,
])
def market_type(request):
    """Parametrized fixture for market types."""
    return request.param


@pytest.fixture(params=["1min", "5min", "15min", "30min", "1hour", "4hour", "1day", "1week"])
def kline_period(request):
    """Parametrized fixture for K-line periods."""
    return request.param


# Test data constants
TEST_SYMBOLS = {
    "valid": [
        ("BTC", "USDT"),
        ("ETH", "USDT"),
        ("LTC", "USDT"),
    ],
    "invalid": [
        ("INVALID", "COIN"),
        ("NONEXISTENT", "TOKEN"),
    ],
}

TEST_LIMITS = {
    "depth": [5, 10, 20, 50],
    "kline": [10, 50, 100],
    "deals": [10, 50, 100],
}

TEST_INTERVALS = ["0", "0.1", "0.01", "1"]