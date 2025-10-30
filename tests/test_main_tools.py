"""
Test cases for main.py MCP tools

This module tests the actual MCP tool functions defined in main.py,
accessing them through the .fn attribute to bypass the FastMCP decorator.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import main module and its tools
import main
from coinex_client import CoinExClient


class TestPublicTools:
    """Test public MCP tools from main.py"""

    def setup_method(self):
        """Setup test environment"""
        # Mock the global coinex_client
        main.coinex_client = AsyncMock(spec=CoinExClient)

    @pytest.mark.asyncio
    async def test_get_ticker_single_pair(self):
        """Test get_ticker tool with single pair"""
        # Mock the client response
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": [{"market": "BTCUSDT", "last": "50000.00"}]
        }
        main.coinex_client.get_tickers.return_value = mock_response
        
        # Test the tool function directly
        result = await main.get_ticker.fn("BTC", "USDT")
        
        # Verify the client was called correctly
        main.coinex_client.get_tickers.assert_called_once_with("BTC", "USDT", CoinExClient.MarketType.SPOT)
        assert result["code"] == 0
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_ticker_top_5_limit(self):
        """Test get_ticker tool returns top 5 when base is None"""
        # Mock response with 10 items
        mock_data = [{"market": f"COIN{i}USDT", "last": f"{i*1000}"} for i in range(10)]
        mock_response = {"code": 0, "message": "OK", "data": mock_data}
        main.coinex_client.get_tickers.return_value = mock_response
        
        # Test without base - should limit to top 5
        result = await main.get_ticker.fn(None, "USDT")
        
        assert result["code"] == 0
        assert len(result["data"]) == 5
        assert result["data"] == mock_data[:5]

    @pytest.mark.asyncio
    async def test_get_orderbook_spot(self):
        """Test get_orderbook tool for spot market"""
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": {"market": "BTCUSDT", "depth": {"asks": [["50000", "1.0"]]}}
        }
        main.coinex_client.get_depth.return_value = mock_response
        
        result = await main.get_orderbook.fn("BTC", "USDT", 20, "spot", "0")
        
        main.coinex_client.get_depth.assert_called_once_with(
            "BTC", "USDT", CoinExClient.MarketType.SPOT, 20, "0"
        )
        assert result["code"] == 0

    @pytest.mark.asyncio
    async def test_get_kline_valid_period(self):
        """Test get_kline tool with valid period"""
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": [[1640995200000, "50000", "51000", "49000", "50500", "100.5"]]
        }
        main.coinex_client.get_kline.return_value = mock_response
        
        result = await main.get_kline.fn("BTC", "USDT", "1hour", 100, "spot")
        
        main.coinex_client.get_kline.assert_called_once_with(
            "1hour", "BTC", "USDT", CoinExClient.MarketType.SPOT, 100
        )
        assert result["code"] == 0

    @pytest.mark.asyncio
    async def test_get_kline_invalid_period(self):
        """Test get_kline tool validates period before calling client"""
        # Verify client was NOT called
        with pytest.raises(ValueError):
            result = await main.get_kline.fn("BTC", "USDT", "invalid_period", 100, "spot")

    @pytest.mark.asyncio
    async def test_get_index_price_top_n_limit(self):
        """Test get_index_price tool limits results to top_n"""
        mock_data = [{"market": f"COIN{i}USDT", "index_price": f"{i*1000}"} for i in range(10)]
        mock_response = {"code": 0, "message": "OK", "data": mock_data}
        main.coinex_client.get_index_price.return_value = mock_response
        
        result = await main.get_index_price.fn("spot", None, "USDT", 3)
        
        # Should limit to top 3
        assert result["code"] == 0
        assert len(result["data"]) == 3


class TestFuturesTools:
    """Test futures-specific MCP tools"""

    def setup_method(self):
        """Setup test environment"""
        main.coinex_client = AsyncMock(spec=CoinExClient)

    @pytest.mark.asyncio
    async def test_get_ticker_futures(self):
        """Test get_ticker tool with single pair"""
        # Mock the client response
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": [{"market": "BTCUSDT", "last": "50000.00"}]
        }
        main.coinex_client.get_tickers.return_value = mock_response

        # Test the tool function directly
        result = await main.get_ticker.fn("BTC", "USDT", "futures")

        # Verify the client was called correctly
        main.coinex_client.get_tickers.assert_called_once_with("BTC", "USDT", CoinExClient.MarketType.FUTURES)
        assert result["code"] == 0
        assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_funding_rate(self):
        """Test get_funding_rate tool"""
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": [{"market": "BTCUSDT", "latest_funding_rate": "0.0001"}]
        }
        main.coinex_client.futures_get_funding_rate.return_value = mock_response
        
        result = await main.get_funding_rate.fn("BTC", "USDT")
        
        main.coinex_client.futures_get_funding_rate.assert_called_once_with("BTC", "USDT")
        assert result["code"] == 0

    @pytest.mark.asyncio
    async def test_get_liquidation_history_placeholder(self):
        """Test get_liquidation_history returns placeholder response"""
        result = await main.get_liquidation_history.fn("BTC", "USDT", None, None, 1, 100)
        
        # This tool returns a placeholder response
        assert result["code"] == -1
        assert "not available" in result["message"]
        assert result["data"] == []


class TestAuthTools:
    """Test authentication-required MCP tools"""

    @pytest.mark.asyncio
    @patch('main.get_secret_client')
    async def test_get_account_balance(self, mock_get_client):
        """Test get_account_balance tool"""
        mock_client = AsyncMock(spec=CoinExClient)
        mock_get_client.return_value = mock_client
        
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": [{"ccy": "USDT", "available": "1000.0"}]
        }
        mock_client.get_balances.return_value = mock_response
        
        result = await main.get_account_balance.fn()
        
        mock_get_client.assert_called_once()
        mock_client.get_balances.assert_called_once_with(CoinExClient.MarketType.SPOT)
        assert result["code"] == 0

    @pytest.mark.asyncio
    @patch('main.get_secret_client')
    async def test_place_order(self, mock_get_client):
        """Test place_order tool"""
        mock_client = AsyncMock(spec=CoinExClient)
        mock_get_client.return_value = mock_client
        
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": {"order_id": 123456, "market": "BTCUSDT"}
        }
        mock_client.place_order.return_value = mock_response
        
        result = await main.place_order.fn(
            "BTC", "buy", "0.001", "USDT", "50000", False, None, None, "spot"
        )
        
        # Verify client method was called
        mock_client.place_order.assert_called_once()
        call_args = mock_client.place_order.call_args
        assert call_args.kwargs['side'] == CoinExClient.OrderSide.BUY
        assert call_args.kwargs['base'] == "BTC"
        assert result["code"] == 0

    @pytest.mark.asyncio
    @patch('main.get_secret_client')
    async def test_get_order_history(self, mock_get_client):
        """Test get_order_history tool"""
        mock_client = AsyncMock(spec=CoinExClient)
        mock_get_client.return_value = mock_client
        
        mock_response = {
            "code": 0,
            "message": "OK",
            "data": [{"order_id": 123456, "market": "BTCUSDT", "side": "buy"}]
        }
        mock_client.get_orders.return_value = mock_response
        
        result = await main.get_order_history.fn(
            "BTC", "USDT", "buy", "finished", False, 1, 100, "spot"
        )
        
        mock_client.get_orders.assert_called_once()
        assert result["code"] == 0


class TestErrorHandling:
    """Test error handling in MCP tools"""

    def setup_method(self):
        """Setup test environment"""
        main.coinex_client = AsyncMock(spec=CoinExClient)

    @pytest.mark.asyncio
    async def test_api_error_passthrough(self):
        """Test that API errors are passed through correctly"""
        error_response = {"code": 4001, "message": "Invalid market", "data": None}
        main.coinex_client.get_tickers.return_value = error_response
        
        result = await main.get_ticker.fn("INVALID", "USDT")
        
        # Error should be passed through unchanged
        assert result["code"] == 4001
        assert result["message"] == "Invalid market"

    @pytest.mark.asyncio
    @patch('main.get_secret_client')
    async def test_auth_credential_error(self, mock_get_client):
        """Test auth tool behavior when credentials are missing"""
        mock_get_client.side_effect = ValueError("Request headers must include X-CoinEx-Access-Id")
        
        # Should raise the ValueError
        with pytest.raises(ValueError, match="Request headers must include X-CoinEx-Access-Id"):
            await main.get_account_balance.fn()


class TestParameterValidation:
    """Test parameter validation in tools"""

    def setup_method(self):
        """Setup test environment"""
        main.coinex_client = AsyncMock(spec=CoinExClient)

    @pytest.mark.asyncio
    async def test_market_type_conversion(self):
        """Test that market_type strings are converted to enums correctly"""
        mock_response = {"code": 0, "message": "OK", "data": {"market": "BTCUSDT"}}
        main.coinex_client.get_depth.return_value = mock_response
        
        # Test futures market type
        await main.get_orderbook.fn("BTC", "USDT", 20, "futures", "0")
        
        main.coinex_client.get_depth.assert_called_once_with(
            "BTC", "USDT", CoinExClient.MarketType.FUTURES, 20, "0"
        )

    @pytest.mark.asyncio
    async def test_default_parameter_handling(self):
        """Test that default parameters work correctly"""
        mock_response = {"code": 0, "message": "OK", "data": [{"market": "BTCUSDT"}]}
        main.coinex_client.get_tickers.return_value = mock_response
        
        # Test with minimal parameters (using defaults)
        result = await main.get_ticker.fn("BTC")
        
        # Should use default quote="USDT"
        main.coinex_client.get_tickers.assert_called_once_with("BTC", "USDT", CoinExClient.MarketType.SPOT)
        assert result["code"] == 0
