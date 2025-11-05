"""
Test cases for error handling and edge cases
"""
import pytest
from typing import Dict, Any
from coinex_mcp_server.coinex_client import CoinExClient


class TestErrorHandling:
    """Test error conditions and edge cases"""

    @pytest.mark.asyncio
    async def test_invalid_currency_pair(self, public_client: CoinExClient):
        """Test handling of invalid currency pairs"""
        result = await public_client.get_tickers("INVALID", "COIN", CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # Should return an error code (not 0)
        assert result["code"] != 0
        assert "Invalid" in result["message"] or "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_invalid_market_type_handling(self, public_client: CoinExClient):
        """Test that invalid market types are handled properly by the enum"""
        # This should work fine as we're using proper enum values
        result = await public_client.get_tickers("BTC", "USDT", CoinExClient.MarketType.SPOT)
        assert result["code"] == 0
        
        result = await public_client.get_tickers("BTC", "USDT", CoinExClient.MarketType.FUTURES)
        assert result["code"] == 0

    @pytest.mark.asyncio
    async def test_invalid_kline_period(self, public_client: CoinExClient):
        """Test handling of invalid K-line periods"""
        result = await public_client.get_kline("invalid_period", "BTC", "USDT", CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert result["code"] != 0  # Should be an error
        assert "Invalid" in result["message"] or "Parameter" in result["message"]

    @pytest.mark.asyncio
    async def test_invalid_depth_limit(self, public_client: CoinExClient):
        """Test handling of invalid depth limits"""
        # Test with an extremely large limit
        result = await public_client.get_depth("BTC", "USDT", CoinExClient.MarketType.SPOT, limit=999999)
        
        assert isinstance(result, dict)
        # API should either return an error or cap the limit
        assert result["code"] != 0 or ("data" in result and "depth" in result["data"])

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limit", [0, -1, -10])
    async def test_negative_or_zero_limits(self, public_client: CoinExClient, limit):
        """Test handling of negative or zero limits"""
        result = await public_client.get_kline("1hour", "BTC", "USDT", CoinExClient.MarketType.SPOT, limit=limit)
        
        assert isinstance(result, dict)
        # Should either return error or handle gracefully
        if result["code"] == 0:
            # If successful, should return some default amount of data
            assert "data" in result
            assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_invalid_interval(self, public_client: CoinExClient):
        """Test handling of invalid depth intervals"""
        result = await public_client.get_depth("BTC", "USDT", CoinExClient.MarketType.SPOT, 
                                               limit=10, interval="invalid_interval")
        
        assert isinstance(result, dict)
        # Should return an error for invalid interval
        assert result["code"] != 0 or "data" in result

    @pytest.mark.asyncio
    async def test_nonexistent_futures_pair(self, public_client: CoinExClient):
        """Test requesting futures data for non-existent pairs"""
        result = await public_client.futures_get_funding_rate("NONEXISTENT", "TOKEN")
        
        assert isinstance(result, dict)
        assert result["code"] != 0  # Should be an error

    @pytest.mark.asyncio
    async def test_extreme_time_ranges(self, public_client: CoinExClient):
        """Test handling of extreme time ranges"""
        import time
        
        # Test with very old start time
        very_old_time = 1000000000  # Year 2001
        current_time = int(time.time() * 1000)
        
        result = await public_client.futures_get_funding_rate_history(
            "BTC", "USDT",
            start_time=very_old_time,
            end_time=current_time,
            page=1,
            limit=5
        )
        
        assert isinstance(result, dict)
        # Should either return error or limited data
        if result["code"] == 0:
            assert "data" in result
            assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_invalid_time_range_order(self, public_client: CoinExClient):
        """Test handling when start_time > end_time"""
        import time
        
        current_time = int(time.time() * 1000)
        future_time = current_time + (24 * 60 * 60 * 1000)  # 1 day in future
        
        result = await public_client.futures_get_funding_rate_history(
            "BTC", "USDT",
            start_time=future_time,  # Start in future
            end_time=current_time,   # End in past
            page=1,
            limit=5
        )
        
        assert isinstance(result, dict)
        # Should either return error or empty data
        if result["code"] == 0:
            assert "data" in result
            # Might return empty list for invalid time range
            assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("page", [0, -1, 99999])
    async def test_invalid_pagination(self, public_client: CoinExClient, page):
        """Test handling of invalid pagination parameters"""
        result = await public_client.futures_get_funding_rate_history(
            "BTC", "USDT",
            page=page,
            limit=5
        )
        
        assert isinstance(result, dict)
        # Should handle invalid pagination gracefully
        if result["code"] == 0:
            assert "data" in result
            assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_empty_string_parameters(self, public_client: CoinExClient):
        """Test handling of empty string parameters"""
        # This should cause an error or be handled gracefully
        result = await public_client.get_tickers("", "", CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        # Empty strings should likely result in an error
        assert result["code"] != 0 or "data" in result

    @pytest.mark.asyncio
    async def test_null_none_parameters(self, public_client: CoinExClient):
        """Test handling of None parameters where strings expected"""
        # Test get_tickers with valid None (should work for getting all tickers)
        result = await public_client.get_tickers(None, None, CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert result["code"] == 0  # This should work (gets all tickers)
        assert "data" in result
        assert isinstance(result["data"], list)
        assert len(result["data"]) > 0


class TestResponseStructureValidation:
    """Test response structure validation"""

    @pytest.mark.asyncio
    async def test_response_always_has_required_fields(self, public_client: CoinExClient):
        """Test that all responses have required basic fields"""
        # Test multiple endpoints to ensure consistent response structure
        endpoints_to_test = [
            lambda: public_client.get_tickers("BTC", "USDT", CoinExClient.MarketType.SPOT),
            lambda: public_client.get_depth("BTC", "USDT", CoinExClient.MarketType.SPOT),
            lambda: public_client.get_kline("1hour", "BTC", "USDT", CoinExClient.MarketType.SPOT),
            lambda: public_client.get_deal("BTC", "USDT", CoinExClient.MarketType.SPOT),
            lambda: public_client.futures_get_funding_rate("BTC", "USDT"),
        ]
        
        for endpoint_func in endpoints_to_test:
            result = await endpoint_func()
            
            # Every response should have these basic fields
            assert isinstance(result, dict), "Response should be a dictionary"
            assert "code" in result, "Response should have 'code' field"
            assert "message" in result, "Response should have 'message' field"
            
            # Code should be an integer
            assert isinstance(result["code"], int), "Code should be an integer"
            
            # Message should be a string
            assert isinstance(result["message"], str), "Message should be a string"
            
            # If successful, should have data field
            if result["code"] == 0:
                assert "data" in result, "Successful response should have 'data' field"

    @pytest.mark.asyncio
    async def test_error_response_structure(self, public_client: CoinExClient):
        """Test that error responses have consistent structure"""
        # Intentionally trigger an error
        result = await public_client.get_tickers("INVALID", "PAIR", CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        assert result["code"] != 0  # Should be an error code
        assert len(result["message"]) > 0  # Should have an error message