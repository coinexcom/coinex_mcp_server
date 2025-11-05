"""
Test cases for CoinEx futures market data APIs
"""
import pytest
from typing import Dict, Any, List
from coinex_mcp_server.coinex_client import CoinExClient


class TestFuturesMarketData:
    """Test futures market data functionality"""

    @pytest.mark.asyncio
    async def test_get_market_info_futures(self, public_client: CoinExClient):
        """Test getting futures market info"""
        result = await public_client.get_market_info("BTC", "USDT", CoinExClient.MarketType.FUTURES)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        market_info = data[0]
        assert isinstance(market_info, dict)
        assert "market" in market_info
        # Market info doesn't include market_type field in API response

    @pytest.mark.asyncio
    async def test_get_tickers_futures(self, public_client: CoinExClient, currency_pair):
        """Test getting futures ticker"""
        base, quote = currency_pair
        result = await public_client.get_tickers(base, quote, CoinExClient.MarketType.FUTURES)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        ticker = data[0]
        assert isinstance(ticker, dict)
        
        # Required futures ticker fields (based on actual API response)
        required_fields = ["market", "last", "open", "high", "low", "volume", "value"]
        for field in required_fields:
            assert field in ticker, f"Missing required futures ticker field: {field}"
        
        assert float(ticker["last"]) > 0
        assert ticker["market"] == f"{base}{quote}"

    @pytest.mark.asyncio
    async def test_get_depth_futures(self, public_client: CoinExClient):
        """Test getting futures order book depth"""
        result = await public_client.get_depth("BTC", "USDT", CoinExClient.MarketType.FUTURES, limit=10)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, dict)
        assert "depth" in data
        assert "market" in data
        
        depth = data["depth"]
        assert "asks" in depth
        assert "bids" in depth

    @pytest.mark.asyncio
    async def test_get_kline_futures(self, public_client: CoinExClient):
        """Test getting futures K-line data"""
        result = await public_client.get_kline("1hour", "BTC", "USDT", CoinExClient.MarketType.FUTURES, limit=5)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 5
        
        if data:
            kline = data[0]
            assert isinstance(kline, dict)
            
            # Required futures K-line fields (based on actual API response)
            required_fields = ["market", "open", "close", "high", "low", "volume", "value", "created_at"]
            for field in required_fields:
                assert field in kline, f"Missing required futures K-line field: {field}"

    @pytest.mark.asyncio
    async def test_get_deal_futures(self, public_client: CoinExClient):
        """Test getting futures recent deals"""
        result = await public_client.get_deal("BTC", "USDT", CoinExClient.MarketType.FUTURES, limit=5)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 5
        
        if data:
            deal = data[0]
            assert isinstance(deal, dict)
            
            # Required futures deal fields (based on actual API response)
            required_fields = ["deal_id", "created_at", "side", "price", "amount"]
            for field in required_fields:
                assert field in deal, f"Missing required futures deal field: {field}"

    @pytest.mark.asyncio
    async def test_get_index_price_futures(self, public_client: CoinExClient):
        """Test getting futures index price"""
        result = await public_client.get_index_price("BTC", "USDT", CoinExClient.MarketType.FUTURES)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        index = data[0]
        assert isinstance(index, dict)
        assert "market" in index
        assert "price" in index
        assert float(index["price"]) > 0


class TestFuturesSpecificFeatures:
    """Test futures-specific features"""

    @pytest.mark.asyncio
    async def test_get_funding_rate(self, public_client: CoinExClient):
        """Test getting current funding rate"""
        result = await public_client.futures_get_funding_rate("BTC", "USDT")
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        funding_rate = data[0]
        assert isinstance(funding_rate, dict)
        
        # Required funding rate fields (based on actual API response)
        required_fields = ["market", "latest_funding_rate", "latest_funding_time"]
        for field in required_fields:
            assert field in funding_rate, f"Missing required funding rate field: {field}"
        
        # Funding rate should be a valid number (can be negative)
        assert isinstance(float(funding_rate["latest_funding_rate"]), float)
        assert isinstance(funding_rate["latest_funding_time"], int)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("base,quote", [("BTC", "USDT"), ("ETH", "USDT")])
    async def test_get_funding_rate_multiple_pairs(self, public_client: CoinExClient, base, quote):
        """Test funding rate for multiple currency pairs"""
        result = await public_client.futures_get_funding_rate(base, quote)
        
        assert result["code"] == 0
        assert len(result["data"]) == 1
        assert result["data"][0]["market"] == f"{base}{quote}"

    @pytest.mark.asyncio
    async def test_get_funding_rate_history(self, public_client: CoinExClient):
        """Test getting funding rate history"""
        result = await public_client.futures_get_funding_rate_history("BTC", "USDT", page=1, limit=5)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 5
        
        if data:
            history_item = data[0]
            assert isinstance(history_item, dict)
            
            # Required funding rate history fields (based on actual API response)
            required_fields = ["actual_funding_rate", "funding_time"]
            for field in required_fields:
                assert field in history_item, f"Missing required funding rate history field: {field}"
            
            assert isinstance(float(history_item["actual_funding_rate"]), float)
            assert isinstance(history_item["funding_time"], int)

    @pytest.mark.asyncio
    async def test_get_premium_history(self, public_client: CoinExClient):
        """Test getting premium index history"""
        result = await public_client.futures_get_premium_history("BTC", "USDT", page=1, limit=5)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 5
        
        if data:
            premium_item = data[0]
            assert isinstance(premium_item, dict)
            
            # Check for expected fields (may vary by API response)
            assert "created_at" in premium_item or "time" in premium_item

    @pytest.mark.asyncio
    async def test_get_basis_history(self, public_client: CoinExClient):
        """Test getting basis history"""
        result = await public_client.futures_basis_index_history("BTC", "USDT")
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        
        if data:
            basis_item = data[0]
            assert isinstance(basis_item, dict)
            # Basis history structure may vary, just ensure it's a valid dict

    @pytest.mark.asyncio
    async def test_get_position_level(self, public_client: CoinExClient):
        """Test getting position levels/margin tiers"""
        result = await public_client.futures_get_position_level("BTC", "USDT")
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 1
        
        position_level = data[0]
        assert isinstance(position_level, dict)
        
        # Check for position level fields
        expected_fields = ["market", "leverage_config"]
        for field in expected_fields:
            if field in position_level:
                assert position_level[field] is not None

    @pytest.mark.asyncio
    async def test_premium_index_history(self, public_client: CoinExClient):
        """Test premium index history (alternative method)"""
        result = await public_client.futures_premium_index_history("BTC", "USDT", page=1, limit=3)
        
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 3

    @pytest.mark.asyncio
    async def test_funding_rate_time_range(self, public_client: CoinExClient):
        """Test funding rate history with time range"""
        import time
        
        # Get data from last 7 days
        end_time = int(time.time() * 1000)
        start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago
        
        result = await public_client.futures_get_funding_rate_history(
            "BTC", "USDT", 
            start_time=start_time, 
            end_time=end_time, 
            page=1, 
            limit=10
        )
        
        assert result["code"] == 0
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        
        # Verify timestamps are within range
        if data:
            for item in data:
                if "funding_time" in item:
                    funding_time = item["funding_time"]
                    assert start_time <= funding_time <= end_time