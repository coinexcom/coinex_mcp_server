"""
Test cases for CoinEx spot market data APIs
"""
import pytest
from typing import Dict, Any, List
from coinex_client import CoinExClient


class TestSpotMarketData:
    """Test spot market data functionality"""

    @pytest.mark.asyncio
    async def test_get_market_info_single(self, public_client: CoinExClient):
        """Test getting single market info"""
        result = await public_client.get_market_info("BTC", "USDT", CoinExClient.MarketType.SPOT)
        
        # Basic response structure assertions
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        # Data structure assertions
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        market_info = data[0]
        assert isinstance(market_info, dict)
        
        # Required fields in market info (based on actual API response)
        required_fields = ["market", "base_ccy", "quote_ccy", "status"]
        for field in required_fields:
            assert field in market_info, f"Missing required field: {field}"
        
        # Verify market info values
        assert market_info["market"] == "BTCUSDT"
        assert market_info["base_ccy"] == "BTC"
        assert market_info["quote_ccy"] == "USDT"

    @pytest.mark.asyncio
    async def test_get_market_info_all(self, public_client: CoinExClient):
        """Test getting all market info"""
        result = await public_client.get_market_info(None, None, CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) > 1000  # Should have many markets
        
        # Check first market structure
        market_info = data[0]
        assert isinstance(market_info, dict)
        assert "market" in market_info

    @pytest.mark.asyncio
    async def test_get_tickers_single(self, public_client: CoinExClient, currency_pair):
        """Test getting single ticker"""
        base, quote = currency_pair
        result = await public_client.get_tickers(base, quote, CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        ticker = data[0]
        assert isinstance(ticker, dict)
        
        # Required ticker fields (based on actual API response)
        required_fields = ["market", "last", "open", "high", "low", "volume", "value", "period"]
        for field in required_fields:
            assert field in ticker, f"Missing required ticker field: {field}"
        
        # Value type assertions
        assert isinstance(ticker["last"], str)  # Price as string
        assert float(ticker["last"]) > 0  # Should be positive
        assert ticker["market"] == f"{base}{quote}"

    @pytest.mark.asyncio
    async def test_get_tickers_all(self, public_client: CoinExClient):
        """Test getting all tickers"""
        result = await public_client.get_tickers(None, None, CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) > 1000  # Should have many tickers

    @pytest.mark.asyncio
    async def test_get_depth(self, public_client: CoinExClient):
        """Test getting order book depth"""
        result = await public_client.get_depth("BTC", "USDT", CoinExClient.MarketType.SPOT, limit=10, interval="0")
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, dict)
        
        # Required depth fields
        required_fields = ["depth", "market", "is_full"]
        for field in required_fields:
            assert field in data, f"Missing required depth field: {field}"
        
        depth = data["depth"]
        assert isinstance(depth, dict)
        assert "asks" in depth
        assert "bids" in depth
        
        # Check asks and bids structure
        asks = depth["asks"]
        bids = depth["bids"]
        assert isinstance(asks, list)
        assert isinstance(bids, list)
        
        if asks:
            ask = asks[0]
            assert isinstance(ask, list)
            assert len(ask) == 2  # [price, quantity]
            assert float(ask[0]) > 0  # Price should be positive
            assert float(ask[1]) > 0  # Quantity should be positive

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limit", [5, 10, 20, 50])
    async def test_get_depth_limits(self, public_client: CoinExClient, limit):
        """Test depth with different limits"""
        result = await public_client.get_depth("BTC", "USDT", CoinExClient.MarketType.SPOT, limit=limit)
        
        assert result["code"] == 0
        depth = result["data"]["depth"]
        
        # The API might return fewer entries than requested, but should not exceed the limit
        if depth["asks"]:
            assert len(depth["asks"]) <= limit
        if depth["bids"]:
            assert len(depth["bids"]) <= limit

    @pytest.mark.asyncio
    async def test_get_kline(self, public_client: CoinExClient):
        """Test getting K-line data"""
        result = await public_client.get_kline("1hour", "BTC", "USDT", CoinExClient.MarketType.SPOT, limit=10)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 10  # Should not exceed requested limit
        
        if data:
            kline = data[0]
            assert isinstance(kline, dict)
            
            # Required K-line fields (based on actual API response)
            required_fields = ["market", "open", "close", "high", "low", "volume", "value", "created_at"]
            for field in required_fields:
                assert field in kline, f"Missing required K-line field: {field}"
            
            # Value type and range assertions
            assert float(kline["open"]) > 0
            assert float(kline["close"]) > 0
            assert float(kline["high"]) >= float(kline["low"])
            assert float(kline["volume"]) >= 0
            assert isinstance(kline["created_at"], int)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("period", ["1min", "5min", "1hour", "1day"])
    async def test_get_kline_periods(self, public_client: CoinExClient, period):
        """Test K-line with different periods"""
        result = await public_client.get_kline(period, "BTC", "USDT", CoinExClient.MarketType.SPOT, limit=5)
        
        assert result["code"] == 0
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        
        if data:
            # API doesn't return period field, but we can verify market field
            assert data[0]["market"] == "BTCUSDT"

    @pytest.mark.asyncio
    async def test_get_deal(self, public_client: CoinExClient):
        """Test getting recent deals"""
        result = await public_client.get_deal("BTC", "USDT", CoinExClient.MarketType.SPOT, limit=10)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 10
        
        if data:
            deal = data[0]
            assert isinstance(deal, dict)
            
            # Required deal fields (based on actual API response)
            required_fields = ["deal_id", "created_at", "side", "price", "amount"]
            for field in required_fields:
                assert field in deal, f"Missing required deal field: {field}"
            
            # Value assertions
            assert deal["side"] in ["buy", "sell"]
            assert float(deal["price"]) > 0
            assert float(deal["amount"]) > 0
            assert isinstance(deal["created_at"], int)

    @pytest.mark.asyncio
    async def test_get_index_price(self, public_client: CoinExClient):
        """Test getting index price"""
        result = await public_client.get_index_price("BTC", "USDT", CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        index = data[0]
        assert isinstance(index, dict)
        
        # Required index fields (based on actual API response)
        required_fields = ["market", "price"]
        for field in required_fields:
            assert field in index, f"Missing required index field: {field}"
        
        assert float(index["price"]) > 0
        assert index["market"] == "BTCUSDT"