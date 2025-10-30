#!/usr/bin/env python3
"""
MCP server for accessing CoinEx cryptocurrency exchange

Notes:
- In HTTP/SSE mode, only tags={"public"} query tools are exposed by default; enable --enable-http-auth to expose tags={"auth"} tools.
- When accessing account/trading tools (tags={"auth"}), provide in request headers:
  - X-CoinEx-Access-Id: Your API Key
  - X-CoinEx-Secret-Key: Your API Secret
- All tools return following CoinEx style: { code: int, message: str, data: any }
"""

import sys
import logging
from typing import Any, Annotated, Literal
from pydantic import Field, validate_call

from fastmcp import FastMCP
from fastmcp.server.auth import StaticTokenVerifier
from fastmcp.server.dependencies import get_http_headers
from coinex_client import CoinExClient, validate_environment
import os
import argparse

# Load .env (won't override externally set environment variables)
try:
    from dotenv import load_dotenv, find_dotenv
    # When started via MCP Inspector, CWD is usually set to project root; find_dotenv is more robust
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path, override=False)
        print(f"Loaded environment variables from {env_path}", file=sys.stderr)
    else:
        print(".env not found, continuing with system environment variables", file=sys.stderr)
except Exception as e:
    # Give hint when python-dotenv is not installed or other exceptions occur, but don't block service
    print(f"Failed to load .env: {e} (you can run pip install python-dotenv)", file=sys.stderr)


# Enum field descriptions (for reuse across tool functions)
MARKET_TYPE_DESC = "Market type: spot|futures|margin; default spot"
ORDER_SIDE_DESC = "Order side: buy|sell"
ORDER_STATUS_DESC = "Order status: pending|finished"

# Initialize FastMCP server
mcp = FastMCP("coinex-mcp-server")

# Delayed initialization: decide whether to allow reading credentials from environment based on transport and auth mode
coinex_client: CoinExClient | None = None
is_http_like: bool = False


def get_secret_client() -> CoinExClient:
    """Get authenticated client based on current transport mode.
    
    - HTTP/SSE mode: Extract credentials from request headers
    - stdio mode: Use global coinex_client with environment credentials
    
    Returns: CoinExClient configured with appropriate credentials.
    """
    if is_http_like:
        # HTTP/SSE mode - extract credentials from request headers
        headers = get_http_headers()  # lowercase dictionary
        access_id = headers.get("x-coinex-access-id")
        secret_key = headers.get("x-coinex-secret-key")

        if not access_id or not secret_key:
            raise ValueError(
                "Request headers must include X-CoinEx-Access-Id and X-CoinEx-Secret-Key to access account/trading interfaces"
            )

        return CoinExClient(access_id=access_id, secret_key=secret_key, enable_env_credentials=False)
    else:
        # stdio mode - use global client with environment credentials
        if coinex_client is None:
            raise ValueError("CoinEx client not initialized")

        # Verify global client has credentials
        if not hasattr(coinex_client, 'access_id') or not coinex_client.access_id:
            raise ValueError(
                "CoinEx API credentials not found. Please set COINEX_ACCESS_ID and COINEX_SECRET_KEY environment variables"
            )

        return coinex_client


# =====================
# Public Market Queries (spot/futures)
# =====================
@mcp.tool(tags={"public"})
@validate_call
async def get_ticker(
    base: Annotated[str | None, Field(description="Base currency, e.g. BTC, ETH; returns top 5 when empty")] = None,
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
) -> dict[str, Any]:
    """Get trading pair's recent price, 24h price and volume information (spot).

    Parameters:
    - base: Optional, base currency like "BTC", "ETH". When not provided, returns top 5 entries.
    - quote: Optional, quote currency, default "USDT".

    Returns: {code, message, data}; when base is not provided, only returns top 5 items.
    """
    api_result = await coinex_client.get_tickers(base, quote, market_type)

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_ticker error, code:{api_result.get('code')}, message:{api_result.get('message')}")
        return api_result

    data = api_result['data']
    if not base and isinstance(data, list):
        api_result['data'] = data[:5]
    return api_result


@mcp.tool(tags={"public"})
@validate_call
async def get_orderbook(
    base: Annotated[str, Field(description="Required, base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    limit: Annotated[int | None, Field(description="Number of price levels to return, options: 5/10/20/50; default 20")] = 20,
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
    interval: Annotated[str | None, Field(description="Merge granularity, default 0; values according to official documentation")] = "0",
) -> dict[str, Any]:
    """Get order book (depth) information (supports spot/futures).

    Parameters:
    - base: Required, base currency. Example: "BTC", "ETH".
    - quote: Optional, quote currency, default "USDT".
    - limit: Optional, number of price levels to return, default 20; valid values: [5, 10, 20, 50].
    - market_type: Optional, market type, default "spot"; valid values: "spot" | "futures".
    - interval: Optional, merge granularity, default "0"; valid values include "0", "0.00000001", ..., "1", "10", "100", "1000" (according to official documentation).

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.get_depth(base, quote, market_type, limit or 20, interval or "0")

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_depth error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
@validate_call
async def get_kline(
    base: Annotated[str, Field(description="Required, base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    period: Annotated[
        Literal["1min", "5min", "15min", "30min", "1hour", "4hour", "1day", "1week"],
        Field(description="K-line period; default 1hour; supports 1min/5min/15min/30min/1hour/4hour/1day/1week")
    ] = "1hour",
    limit: Annotated[int | None, Field(description="Number of records to return; default 100")] = 100,
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
) -> dict[str, Any]:
    """Get K-line data (supports spot/futures).

    Parameters:
    - base: Required, base currency. Example: "BTC", "ETH".
    - quote: Optional, quote currency, default "USDT".
    - period: Optional, K-line period, default "1hour";
      - Spot/futures common period whitelist: "1min","5min","15min","30min","1hour","4hour","1day","1week".
    - limit: Optional, number of records, default 100.
    - market_type: Optional, market type, default "spot"; options: "spot" | "futures".

    Error: When period is not in whitelist, returns {code:-1, message:"Unsupported time period"}.
    Returns: {code, message, data}.
    """
    valid_periods = ["1min", "5min", "15min", "30min", "1hour", "4hour", "1day", "1week"]

    if period not in valid_periods:
        return {"code": -1, "message": f"Unsupported time period: {period}."}

    api_result = await coinex_client.get_kline(str(period), base, quote, market_type, limit)

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_kline error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


# ===============
# Additional Public Tools
# ===============

@mcp.tool(tags={"public"})
@validate_call
async def list_markets(
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
    base: Annotated[str | None, Field(description="Optional; base currency to filter")] = None,
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
) -> dict[str, Any]:
    """List market status (spot/futures).

    Parameters:
    - market_type: Optional, default "spot"; options: "spot" | "futures".
    - base: Optional, base currency to filter.
    - quote: Optional, quote currency, default "USDT".

    Returns: {code, message, data} (list).
    """
    api_result = await coinex_client.get_market_info(base, quote, market_type)
    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"list_markets error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
@validate_call
async def get_deals(
    base: Annotated[str, Field(description="Required, base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
    limit: Annotated[int | None, Field(description="Return quantity, default 100, max 1000 (per official docs)")] = 100,
) -> dict[str, Any]:
    """Get recent trades (deals).

    Parameters:
    - base: Required, base currency.
    - quote: Optional, quote currency, default "USDT".
    - market_type: Optional, default "spot"; options: "spot" | "futures".
    - limit: Optional, return quantity, default 100, max 1000 (per official documentation).

    Returns: {code, message, data} (list).
    """
    api_result = await coinex_client.get_deal(base, quote, market_type, limit)

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_deals error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
@validate_call
async def get_index_price(
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
    base: Annotated[str | None, Field(description="Optional; base currency, returns multi-market index if not provided")] = None,
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    top_n: Annotated[int | None, Field(description="Return top N entries when base not provided; default 5")] = 5,
) -> dict[str, Any]:
    """Get market index price (spot/futures). Supports batch; returns top N entries when base not provided.

    Parameters:
    - market_type: Optional, default "spot"; options: "spot" | "futures".
    - base: Optional, base currency; returns multi-market index when not provided.
    - quote: Optional, quote currency, default "USDT".
    - top_n: Optional, only effective when base not provided; default 5.

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.get_index_price(base, quote, market_type)

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_index_price error, code:{api_result.get('code')}, message:{api_result.get('message')}")
        return api_result

    if not base and isinstance(api_result.get('data'), list) and top_n:
        api_result['data'] = api_result['data'][:top_n]
    return api_result


# ====== Futures-Specific ======

@mcp.tool(tags={"public"})
async def get_funding_rate(
    base: Annotated[str, Field(description="Required, futures base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT"
) -> dict[str, Any]:
    """Get current funding rate (futures only).

    Parameters:
    - base: Required, futures base currency, e.g. "BTC", "ETH".
    - quote: Optional, quote currency, default "USDT".

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.futures_get_funding_rate(base, quote)
    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_funding_rate error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
async def get_funding_rate_history(
    base: Annotated[str, Field(description="Required, futures base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    start_time: Annotated[int | None, Field(description="Start timestamp (milliseconds)")] = None,
    end_time: Annotated[int | None, Field(description="End timestamp (milliseconds)")] = None,
    page: Annotated[int | None, Field(description="Page number; default 1")] = 1,
    limit: Annotated[int | None, Field(description="Number of records; default 100")] = 100,
) -> dict[str, Any]:
    """Get funding rate history (futures only).

    Parameters:
    - base: Required, futures base currency.
    - quote: Optional, quote currency, default "USDT".
    - start_time: Optional, start timestamp (milliseconds).
    - end_time: Optional, end timestamp (milliseconds).
    - page: Optional, default 1.
    - limit: Optional, default 100.

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.futures_get_funding_rate_history(base, quote, start_time, end_time, page, limit)
    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_funding_rate_history error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
async def get_premium_index_history(
    base: Annotated[str, Field(description="Required, futures base currency")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    start_time: Annotated[int | None, Field(description="Start timestamp (milliseconds)")] = None,
    end_time: Annotated[int | None, Field(description="End timestamp (milliseconds)")] = None,
    page: Annotated[int | None, Field(description="Page number; default 1")] = 1,
    limit: Annotated[int | None, Field(description="Number of records; default 100")] = 100,
) -> dict[str, Any]:
    """Get premium index history (futures only).

    Parameters:
    - base: Required, futures base currency.
    - quote: Optional, quote currency, default "USDT".
    - start_time: Optional, start timestamp (milliseconds).
    - end_time: Optional, end timestamp (milliseconds).
    - page: Optional, default 1.
    - limit: Optional, default 100.

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.futures_get_premium_history(base, quote, start_time, end_time, page, limit)
    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_premium_index_history error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
async def get_basis_history(
    base: Annotated[str, Field(description="Required, futures base currency")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    start_time: Annotated[int | None, Field(description="Start timestamp (milliseconds)")] = None,
    end_time: Annotated[int | None, Field(description="End timestamp (milliseconds)")] = None,
    page: Annotated[int | None, Field(description="Placeholder parameter (currently unused)")] = 1,
    limit: Annotated[int | None, Field(description="Placeholder parameter (currently unused)")] = 100,
) -> dict[str, Any]:
    """Get basis history (futures only).

    Parameters:
    - base: Required, futures base currency.
    - quote: Optional, quote currency, default "USDT".
    - start_time: Optional, start timestamp (milliseconds).
    - end_time: Optional, end timestamp (milliseconds).
    - page: Optional, placeholder parameter (currently unused by client).
    - limit: Optional, placeholder parameter (currently unused by client).

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.futures_basis_index_history(base, quote, start_time, end_time, page, limit)
    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_basis_history error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
async def get_margin_tiers(
    base: Annotated[str, Field(description="Required, futures base currency")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT"
) -> dict[str, Any]:
    """Get margin tiers/ position levels (futures only).

    Parameters:
    - base: Required, futures base currency.
    - quote: Optional, quote currency, default "USDT".

    Returns: {code, message, data}.
    """
    api_result = await coinex_client.futures_get_position_level(base, quote)
    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_position_tiers error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"public"})
async def get_liquidation_history(
    base: Annotated[str, Field(description="Required, futures base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    start_time: Annotated[int | None, Field(description="Start timestamp (milliseconds)")] = None,
    end_time: Annotated[int | None, Field(description="End timestamp (milliseconds)")] = None,
    page: Annotated[int | None, Field(description="Page number; default 1")] = 1,
    limit: Annotated[int | None, Field(description="Number of records; default 100")] = 100,
) -> dict[str, Any]:
    """Get liquidation history (futures only).

    Parameters:
    - base: Required, futures base currency.
    - quote: Optional, quote currency, default "USDT".
    - start_time: Optional, start timestamp (milliseconds).
    - end_time: Optional, end timestamp (milliseconds).
    - page: Optional, page number, default 1.
    - limit: Optional, number of records, default 100.

    Returns: {code, message, data}.
    """
    # Note: This function doesn't exist in the new API, return a placeholder response
    return {"code": -1, "message": "Liquidation history not available in current API version", "data": []}


@mcp.tool(tags={"auth"})
async def get_account_balance() -> dict[str, Any]:
    """Get account balance information (requires authentication).

    Usage (HTTP/SSE): Include in request headers:
    - X-CoinEx-Access-Id
    - X-CoinEx-Secret-Key

    Returns: {code, message, data}.
    """
    client = get_secret_client()
    api_result = await client.get_balances(CoinExClient.MarketType.SPOT)

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"get_balances error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"auth"})
@validate_call
async def place_order(
    base: Annotated[str, Field(description="Required, base currency, e.g. BTC, ETH")],
    side: Annotated[CoinExClient.OrderSide, Field(description=ORDER_SIDE_DESC)],
    amount: Annotated[str, Field(description="Required, order quantity (string), must meet precision and minimum volume requirements")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    price: Annotated[str | None, Field(description="Optional; if provided, creates a limit order, otherwise market order")] = None,
    is_hide: Annotated[bool | None, Field(description="Optional, whether to place a hidden order")] = None,
    client_id: Annotated[str | None, Field(description="Optional, custom order ID")] = None,
    trigger_price: Annotated[str | None, Field(description="Optional, if provided, creates a stop order based on it")] = None,
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
) -> dict[str, Any]:
    """Place trading order (requires authentication, real funds).
    Strong reminder: This is a real money trading operation. Please confirm with end user again before calling!

    Parameters:
    - base: Required, base currency.
    - side: Required, direction: buy|sell.
    - amount: Required, order quantity (string).
    - quote: Optional, quote currency, default "USDT".
    - price: Optional; if provided, creates limit order, otherwise market order.
    - is_hide: Optional, whether to place a hidden order.
    - client_id: Optional, custom order ID.
    - trigger_price: Optional, if provided, creates a stop order.
    - market_type: Optional, market type, default "spot".

    Returns: {code, message, data}. Logs error on failure.
    """
    client = get_secret_client()
    
    api_result = await client.place_order(
        side=side,
        base=base,
        quote=quote,
        amount=amount,
        market_type=market_type,
        price=price,
        is_hide=is_hide,
        client_id=client_id,
        trigger_price=trigger_price
    )

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"place_order error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"auth"})
@validate_call
async def cancel_order(
    base: Annotated[str, Field(description="Required, base currency, e.g. BTC, ETH")],
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    order_id: Annotated[int, Field(description="Optional, order ID to cancel, if empty, cancels all orders")] = None,
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
) -> dict[str, Any]:
    """Cancel order (requires authentication).

    Parameters:
    - base: Required, base currency.
    - order_id: Optional, order ID to cancel, if empty, cancels all orders.
    - quote: Optional, quote currency, default "USDT".
    - market_type: Optional, market type, default "spot".

    Returns: {code, message, data}.
    """
    client = get_secret_client()
    api_result = await client.cancel_order(base, quote, market_type, order_id)

    if api_result.get('code') != 0 or 'data' not in api_result:
        logging.error(f"cancel_order error, code:{api_result.get('code')}, message:{api_result.get('message')}")
    return api_result


@mcp.tool(tags={"auth"})
@validate_call
async def get_order_history(
    base: Annotated[str | None, Field(description="Optional, base currency; query all markets if empty")] = None,
    quote: Annotated[str, Field(description="Quote currency, default USDT")] = "USDT",
    side: Annotated[CoinExClient.OrderSide | None, Field(description=ORDER_SIDE_DESC)] = None,
    status: Annotated[CoinExClient.OrderStatus, Field(description=ORDER_STATUS_DESC)] = CoinExClient.OrderStatus.FINISHED,
    is_stop: Annotated[bool | None, Field(description="Optional, whether to query stop orders; default False")] = False,
    page: Annotated[int | None, Field(description="Optional, page number; default 1")] = 1,
    limit: Annotated[int | None, Field(description="Optional, total return limit; default 100")] = 100,
    market_type: Annotated[CoinExClient.MarketType, Field(description=MARKET_TYPE_DESC)] = CoinExClient.MarketType.SPOT,
) -> dict[str, Any]:
    """Get order history (requires authentication).

    Description: Returns list of orders; limit applies to total merged count.

    Parameters:
    - base: Optional, base currency; queries all markets if empty.
    - quote: Optional, quote currency, default "USDT".
    - side: Optional, order side.
    - status: Optional, order status, pending(open) or finished, default 'finished'.
    - is_stop: Optional, whether to query stop orders, default False.
    - page: Optional, page number, default 1.
    - limit: Optional, default 100.
    - market_type: Optional, market type, default "spot".

    Returns: {code, message, data}, sorted by time descending (determined by server/API).
    """
    client = get_secret_client()
    
    api_result = await client.get_orders(
        base, quote, market_type, side, status, is_stop, page, limit
    )
    return api_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CoinEx FastMCP server startup parameters")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http", "streamable-http", "sse"],
        default="stdio",
        help="Transport protocol: stdio(default) | http(equivalent to streamable-http) | streamable-http | sse",
    )
    parser.add_argument("--host", default=None, help="HTTP service bind address (only valid in http/streamable-http mode)")
    parser.add_argument("--port", type=int, default=None, help="HTTP service port (only valid in http/streamable-http mode)")
    parser.add_argument(
        "--path",
        default=None,
        help="Endpoint path: /mcp path in http/streamable-http mode; mount path in sse mode",
    )
    parser.add_argument(
        "--enable-http-auth",
        action="store_true",
        help="Enable HTTP-based authentication and sensitive tools (default off, only exposes query tools)",
    )
    # Added: Worker processes and port reuse (only valid in HTTP/SSE mode)
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes in HTTP/SSE mode (managed by underlying uvicorn)",
    )
    parser.add_argument(
        "--reuse-port",
        action="store_true",
        help="Enable SO_REUSEPORT for multi-process (use with caution, only when multiple independent processes need to share same port)",
    )
    args = parser.parse_args()

    # Compatible with common "http" notation in documentation
    transport = args.transport
    if transport == "http":
        transport = "streamable-http"

    # Calculate HTTP auth switch: default off; only enable when explicitly turned on via command line or environment variable
    env_http_auth_enabled = os.getenv("HTTP_AUTH_ENABLED", "false").lower() in ("1", "true", "yes", "on")
    http_auth_enabled = args.enable_http_auth or env_http_auth_enabled

    # Apply switch under HTTP/SSE transport
    is_http_like = transport in ("streamable-http", "sse")

    # Initialize client for public data access based on mode (will not carry credentials)
    if is_http_like:
        # Disable environment credential fallback in any HTTP/SSE mode
        coinex_client = CoinExClient(enable_env_credentials=False)
        print("HTTP/SSE mode: Environment credential fallback disabled.", file=sys.stderr)
    else:
        # Only non-HTTP mode allows loading from environment (common scenario for local stdio development/self-hosting)
        coinex_client = CoinExClient(enable_env_credentials=True)
        has_credentials = validate_environment()
        if not has_credentials:
            print("Error: CoinEx API credentials not found, some features will be unavailable", file=sys.stderr)

    if is_http_like:
        if not http_auth_enabled:
            # Only expose public tag tools
            mcp.include_tags = {"public"}
            print("HTTP authentication disabled: Only exposing query tools (public)", file=sys.stderr)
        else:
            # Optional: Enable Bearer authentication based on environment variables (static Token)
            API_TOKEN = os.getenv("API_TOKEN")
            if API_TOKEN:
                scopes_env = os.getenv("API_SCOPES", "").replace(",", " ").split()
                mcp.auth = StaticTokenVerifier(
                    tokens={
                        API_TOKEN: {
                            "client_id": "api-token",
                            "scopes": scopes_env,
                        }
                    },
                    required_scopes=scopes_env or None,
                )
                print("Bearer authentication enabled (API_TOKEN)", file=sys.stderr)

    # Assemble uvicorn configuration (only effective in HTTP/SSE mode)
    uvicorn_config = None
    if is_http_like:
        uvicorn_config = {}
        if args.workers is not None:
            uvicorn_config["workers"] = args.workers
        if args.reuse_port:
            uvicorn_config["reuse_port"] = True
        # If finally empty, change to None to avoid passing empty configuration
        if not uvicorn_config:
            uvicorn_config = None

    # Start (2.x: only pass HTTP params for HTTP transports)
    if transport == "stdio":
        mcp.run(transport=transport)
    else:
        mcp.run(
            transport=transport,
            host=args.host,
            port=args.port,
            path=args.path,
            # Only pass when configured, avoid affecting stdio
            **({"uvicorn_config": uvicorn_config} if uvicorn_config is not None else {})
        )
