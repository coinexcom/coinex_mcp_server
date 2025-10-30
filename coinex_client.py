"""
CoinEx API Client
Implements authentication, signing and request functionality for CoinEx API v2
"""

import os
import time
import hmac
import hashlib
import json
from enum import Enum
from typing import Any, Dict, Optional, List
from urllib.parse import urlencode
import httpx


class CoinExClient:
    """CoinEx API Client"""
    class MarketType(Enum):
        SPOT = "spot"
        MARGIN = "margin"
        FUTURES = "futures"

    class OrderType(Enum):
        LIMIT = "limit"
        MARKET = "market"

    class OrderSide(Enum):
        BUY = "buy"
        SELL = "sell"

    class OrderStatus(Enum):
        PENDING = "pending"
        FINISHED = "finished"

    def __init__(self, access_id: str = None, secret_key: str = None, *, enable_env_credentials: bool = True):
        """Initialize CoinEx client
        :param access_id: API access ID
        :param secret_key: API secret key
        :param enable_env_credentials: Whether to allow fallback reading from environment variables COINEX_ACCESS_ID/COINEX_SECRET_KEY
        """

        if enable_env_credentials:
            self.access_id = access_id or os.getenv('COINEX_ACCESS_ID')
            self.secret_key = secret_key or os.getenv('COINEX_SECRET_KEY')
        else:
            # Strictly use passed parameters, do not take over from environment
            self.access_id = access_id
            self.secret_key = secret_key
        self.base_url = "https://api.coinex.com"  # CoinEx doesn't have a dedicated testnet, use mainnet
        self.timeout = 30

    def _generate_signature(self, method: str, path: str, params: Dict = None, body: str = "") -> tuple[str, str]:
        """Generate API signature"""
        if not self.secret_key:
            raise ValueError("secret_key is required to generate signature")

        timestamp = str(int(time.time() * 1000))

        # Build string to be signed
        if params:
            query_string = urlencode(params)
            prepared_str = f"{method}{path}?{query_string}{body}{timestamp}"
        else:
            prepared_str = f"{method}{path}{body}{timestamp}"

        # Generate signature using HMAC-SHA256
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            prepared_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature, timestamp

    def _get_headers(self, method: str, path: str, params: Dict = None, body: str = "") -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "coinex-mcp-server/1.0"
        }

        # If authentication information is available, add signature headers
        if self.access_id and self.secret_key:
            signature, timestamp = self._generate_signature(method, path, params, body)
            headers.update({
                "X-COINEX-KEY": self.access_id,
                "X-COINEX-SIGN": signature,
                "X-COINEX-TIMESTAMP": timestamp
            })

        return headers

    # --------------------
    # Generic public market query helpers
    # --------------------
    @classmethod
    def _market_type_str_in_path(cls, market_type: MarketType) -> str:
        return market_type.value if market_type != cls.MarketType.MARGIN else cls.MarketType.SPOT.value

    @classmethod
    def _build_market_path(cls, market_type: MarketType, endpoint: str) -> str:
        """Assemble generic path, e.g. endpoint='market' -> '/v2/spot/market'."""
        mt = cls._market_type_str_in_path(market_type)
        endpoint = endpoint.lstrip('/')
        return f"/v2/{mt}/{endpoint}"

    # Unified: public market queries (spot/futures routing)
    async def _market_request(self, endpoint: str, method: str = 'GET', base_currency: Optional[str] = None,
                              quote_currency: Optional[str] = None, market_type: MarketType = MarketType.SPOT,
                              extra_params: Optional[Dict[str, Any]] = None):
        """Unified market request with market type routing and symbol normalization.
        - market_type: 'spot' | 'futures'
        - endpoint: e.g. 'market', 'ticker', 'order', 'cancel-order', 'deals', 'depth', 'kline'
        - method: HTTP method 'GET' | 'POST' | 'DELETE', default 'GET'
        - markets: str or [str], market symbol(s), maybe needs to be normalized
        - extra_params: additional query parameters, such as limit/interval/period
        """
        path = self._build_market_path(market_type, endpoint)

        data: Dict[str, Any] = {}

        if base_currency and not quote_currency or quote_currency and not base_currency:
            raise ValueError(f"Base currency is '{base_currency}' and quote_currency is {quote_currency}, this is meaningless!")

        if base_currency and quote_currency:
            market = base_currency + quote_currency
            data['market'] = market

        if extra_params:
            data.update(extra_params)

        return await self._request(method, path, data=data)

    async def _request(self, method: str, path: str, data: Dict = None) -> Dict[str, Any]:
        """Send HTTP request

        :param method: HTTP method (GET/POST/DELETE)
        :param path: API path
        :param data: Request data - for GET requests becomes URL params, for POST/DELETE becomes request body
        """
        url = f"{self.base_url}{path}"

        # Determine params and body based on HTTP method
        params = None
        request_body = ""

        if method.upper() == "GET":
            # GET requests use URL parameters
            params = data
        else:
            # POST/DELETE requests use request body
            if data:
                request_body = json.dumps(data, separators=(',', ':'))

        # Get request headers
        headers = self._get_headers(method, path, params, request_body)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            """Send HTTP request"""
            try:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, content=request_body)
                else:
                    # coinex api doesn't have DELETE/PUT requests
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                raise Exception("Request timeout")
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP error {e.response.status_code}"
                try:
                    error_data = e.response.json()
                    if 'message' in error_data:
                        error_msg += f": {error_data['message']}"
                except (ValueError, KeyError, AttributeError):
                    pass
                raise Exception(error_msg)
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")

    # =====================
    # Unified public market queries
    # =====================
    async def get_market_info(self, base: str | None = None, quote: str | None = None, market_type: MarketType | None = None) -> Dict[str, Any]:
        return await self._market_request('market', base_currency=base, quote_currency=quote, market_type=market_type)

    async def get_tickers(self, base: str | None = None, quote: str | None = None, market_type: MarketType | None = None) -> Dict[str, Any]:
        return await self._market_request('ticker', base_currency=base, quote_currency=quote, market_type=market_type)

    async def get_depth(self, base: str, quote: str = 'USDT', market_type: MarketType | None = None, limit: int = 20, interval: str = "0") -> Dict[str, Any]:
        extra = {"limit": limit, "interval": interval}
        return await self._market_request('depth', base_currency=base, quote_currency=quote, market_type=market_type,
                                          extra_params=extra)

    async def get_kline(self, period: str, base: str, quote: str = 'USDT', market_type: MarketType | None = None, limit: int = 100) -> Dict[str, Any]:
        extra = {"period": period, "limit": limit}
        return await self._market_request('kline', base_currency=base, quote_currency=quote, market_type=market_type,
                                          extra_params=extra)

    async def get_deal(self, base: str, quote: str = 'USDT', market_type: MarketType | None = None, limit: int = 100) -> Dict[str, Any]:
        return await self._market_request('deals', base_currency=base, quote_currency=quote, market_type=market_type,
                                          extra_params={"limit": limit})

    async def get_index_price(self, base: str, quote: str = 'USDT', market_type: MarketType | None = None) -> Dict[str, Any]:
        return await self._market_request('index', base_currency=base, quote_currency=quote, market_type=market_type)

    # =====================
    # Futures public market queries
    # =====================
    async def futures_get_funding_rate(self, base: str, quote: str = 'USDT'):
        """Get current funding rate (futures)"""
        return await self._market_request("funding-rate", base_currency=base, quote_currency=quote, market_type=self.MarketType.FUTURES)

    async def futures_get_funding_rate_history(self, base: str, quote: str = 'USDT',
                                               start_time: Optional[int] = None,
                                               end_time: Optional[int] = None, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get funding rate history (futures)"""
        extra_params: Dict[str, Any] = {"page": page, "limit": limit}
        if start_time is not None:
            extra_params["start_time"] = start_time
        if end_time is not None:
            extra_params["end_time"] = end_time
        return await self._market_request("funding-rate-history",
                                          base_currency=base, quote_currency=quote, market_type=self.MarketType.FUTURES,
                                          extra_params=extra_params)

    async def futures_get_premium_history(self, base: str, quote: str = 'USDT',
                                          start_time: Optional[int] = None, end_time: Optional[int] = None,
                                          page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get premium index history (futures)"""
        extra_params: Dict[str, Any] = {"page": page, "limit": limit}
        if start_time is not None:
            extra_params["start_time"] = start_time
        if end_time is not None:
            extra_params["end_time"] = end_time
        return await self._market_request("premium-index-history",
                                          base_currency=base, quote_currency=quote, market_type=self.MarketType.FUTURES,
                                          extra_params=extra_params)

    async def futures_get_position_level(self, base: str, quote: str = 'USDT') -> Dict[str, Any]:
        """Get position levels (futures)"""
        return await self._market_request("position-level", base_currency=base, quote_currency=quote,
                                          market_type=self.MarketType.FUTURES)

    async def futures_premium_index_history(self, base: str, quote: str = 'USDT',
                                            start_time: Optional[int] = None, end_time: Optional[int] = None,
                                            page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get premium index history (futures)"""
        extra_params: Dict[str, Any] = {"page": page, "limit": limit}
        if start_time is not None:
            extra_params["start_time"] = start_time
        if end_time is not None:
            extra_params["end_time"] = end_time
        return await self._market_request("premium-index-history",
                                          base_currency=base, quote_currency=quote, market_type=self.MarketType.FUTURES,
                                          extra_params=extra_params)

    async def futures_basis_index_history(self, base: str, quote: str = 'USDT',
                                          start_time: Optional[int] = None, end_time: Optional[int] = None,
                                          page: int = 1, limit: int = 10) -> Dict[str, Any]:
        extra_params: Dict[str, Any] = {"page": page, "limit": limit}
        if start_time is not None:
            extra_params["start_time"] = start_time
        if end_time is not None:
            extra_params["end_time"] = end_time
        return await self._market_request("basis-history",
                                          base_currency=base, quote_currency=quote, market_type=self.MarketType.FUTURES,
                                          extra_params=extra_params)

    # =====================
    # personal account info( require authentication)
    # =====================
    # Account interfaces
    async def get_balances(self, market_type: MarketType = MarketType.SPOT) -> Dict[str, Any]:
        """Get account balance"""
        if not self.access_id or not self.secret_key:
            raise ValueError("Account interface requires access_id and secret_key")

        path = f"/v2/assets/{self._market_type_str_in_path(market_type)}/balance"
        return await self._request("GET", path, data=None)

    # Trading interfaces (authentication required)
    async def place_order(self, side: OrderSide, base: str, quote: str, amount: str,
                          market_type: MarketType = MarketType.SPOT,
                          price: str = None,
                          is_hide: bool = None, client_id: str = None,
                          trigger_price: str = None, stp_mode: str = None) -> Dict[str, Any]:
        """Place order.
        This is an important interface that involves fund operations, so both the base and quote parameters must be explicitly specified by the user.
        Parameters:
            side: buy/sell
            base: base currency
            quote: quote currency
            amount: order quantity (string), must meet precision and minimum volume requirements
            market_type: spot/futures/margin
            price: optional, if provided, creates a limit order; otherwise, creates a market order
            is_hide: optional, if True, places a hidden order
            trigger_price: optional, if provided, creates a stop order
            stp_mode: optional, self-trade prevention mode
            client_id: optional, custom order ID
        """
        if not self.access_id or not self.secret_key:
            raise ValueError("Trading interface requires access_id and secret_key")

        params = {
            "market_type": market_type.name,
            "side": side.value,
            "amount": amount,
        }

        if price:
            params["price"] = price
            params["type"] = self.OrderType.LIMIT.value
        else:
            params["type"] = self.OrderType.MARKET.value

        if client_id:
            params["client_id"] = client_id
        if is_hide:
            params["is_hide"] = 'true'

        if trigger_price:
            params["trigger_price"] = trigger_price
            if stp_mode:
                params["stp_mode"] = stp_mode

        endpoint = 'stop-order' if trigger_price else "order"

        return await self._market_request(endpoint, 'POST', base, quote,
                                          market_type=market_type, extra_params=params)

    # Trading interfaces (authentication required)
    async def cancel_order(self, base: str, quote: str, market_type: MarketType = MarketType.SPOT,
                           order_id: int | None = None) -> Dict[str, Any]:
        """Cancel an order or all orders in a market.
        This is an important interface that involves fund operations, so both the base and quote parameters must be explicitly specified by the user.
        Parameters:
            base: base currency
            quote: quote currency
            market_type: spot/futures/margin
            order_id: optional, if provided, cancels the specific order; otherwise, cancels all orders in the market
        """
        if not self.access_id or not self.secret_key:
            raise ValueError("Trading interface requires access_id and secret_key")
        endpoint = "cancel-order" if order_id else "cancel-all-orders"
        params: Dict[str, Any] = {"market_type": market_type.name}
        if order_id:
            params["order_id"] = order_id
        return await self._market_request(endpoint, 'POST', base, quote,
                                          market_type=market_type, extra_params=params)

    # Trading interfaces (authentication required)
    async def get_orders(self, base: str = None, quote: str = None,
                         market_type: MarketType = MarketType.SPOT,
                         side: OrderSide = None,
                         status: OrderStatus = OrderStatus.FINISHED,
                         is_stop=False,
                         page: int = 1, limit: int = 100) -> Dict[str, Any]:
        if not self.access_id or not self.secret_key:
            raise ValueError("Account interface requires access_id and secret_key")

        extra_params = {
            "market_type": market_type.value,
            "page": page,
            "limit": limit
        }
        if side:
            extra_params["side"] = side.value

        stop_seg = "stop-" if is_stop else ""
        endpoint = f"{status.value}-{stop_seg}order"
        return await self._market_request(endpoint, 'GET', base, quote,
                                          market_type=market_type, extra_params=extra_params)


def validate_environment():
    """Validate environment variable configuration"""
    access_id = os.getenv('COINEX_ACCESS_ID')
    secret_key = os.getenv('COINEX_SECRET_KEY')

    if not access_id or not secret_key:
        print("Warning: COINEX_ACCESS_ID and COINEX_SECRET_KEY environment variables not set")
        print("Some features (account info, trading) will be unavailable")
        print("Market data features can still be used normally")
        return False

    return True
