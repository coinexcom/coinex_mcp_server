"""
Test cases for authentication-required features
"""
import pytest
import os
from typing import Dict, Any
from dotenv import load_dotenv
from coinex_mcp_server.coinex_client import CoinExClient

# Load environment variables from .env file
load_dotenv()


class TestAuthenticationRequired:
    """Test features that require authentication"""

    @pytest.mark.asyncio
    async def test_get_balances_spot(self, auth_client: CoinExClient, has_auth_credentials):
        """Test getting spot account balances - should succeed with valid credentials"""
        if not has_auth_credentials:
            pytest.skip("Skipping authentication test - no API credentials provided")
        
        result = await auth_client.get_balances(CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # With valid credentials, this should succeed
        assert result["code"] == 0, f"Expected success but got error: {result.get('message', 'Unknown error')}"
        assert result["message"] == "OK"
        assert "data" in result
        
        data = result["data"]
        assert isinstance(data, list)
        
        # Should have balance information structure
        # Data is a list of balance objects
        for balance_info in data:
            if balance_info:  # Some currencies might have None/empty balance
                assert isinstance(balance_info, dict)
                # Common balance fields might include 'available', 'frozen', 'ccy', etc.
                assert 'ccy' in balance_info
                assert 'available' in balance_info

    @pytest.mark.asyncio
    async def test_get_balances_futures(self, auth_client: CoinExClient, has_auth_credentials):
        """Test getting futures account balances - should succeed with valid credentials"""
        if not has_auth_credentials:
            pytest.skip("Skipping authentication test - no API credentials provided")
        
        result = await auth_client.get_balances(CoinExClient.MarketType.FUTURES)
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # With valid credentials, this should succeed
        assert result["code"] == 0, f"Expected success but got error: {result.get('message', 'Unknown error')}"
        assert "data" in result
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio 
    async def test_get_orders_finished(self, auth_client: CoinExClient, has_auth_credentials):
        """Test getting finished orders - should succeed with valid credentials"""
        if not has_auth_credentials:
            pytest.skip("Skipping authentication test - no API credentials provided")
        
        result = await auth_client.get_orders(
            market_type=CoinExClient.MarketType.SPOT,
            status=CoinExClient.OrderStatus.FINISHED,
            limit=5
        )
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # With valid credentials, this should succeed
        assert result["code"] == 0, f"Expected success but got error: {result.get('message', 'Unknown error')}"
        assert "data" in result
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) <= 5
        
        # Check order structure if any orders exist
        if data:
            order = data[0]
            assert isinstance(order, dict)
            
            # Common order fields
            expected_fields = ["market", "side", "amount", "price"]
            for field in expected_fields:
                assert field in order, f"Missing order field: {field}"
                
            assert order["side"] in ["buy", "sell"]
            assert float(order["amount"]) > 0

    @pytest.mark.asyncio
    async def test_get_orders_pending(self, auth_client: CoinExClient, has_auth_credentials):
        """Test getting pending orders - should succeed with valid credentials"""
        if not has_auth_credentials:
            pytest.skip("Skipping authentication test - no API credentials provided")
        
        result = await auth_client.get_orders(
            "BTC", "USDT",
            CoinExClient.MarketType.SPOT,
            status=CoinExClient.OrderStatus.PENDING,
            limit=5
        )
        
        assert isinstance(result, dict)
        assert "code" in result
        
        # With valid credentials, this should succeed
        assert result["code"] == 0, f"Expected success but got error: {result.get('message', 'Unknown error')}"
        assert "data" in result
        assert isinstance(result["data"], list)

    @pytest.mark.asyncio
    async def test_get_orders_with_side_filter(self, auth_client: CoinExClient, has_auth_credentials):
        """Test getting orders with side filter - should succeed with valid credentials"""
        if not has_auth_credentials:
            pytest.skip("Skipping authentication test - no API credentials provided")
        
        for side in [CoinExClient.OrderSide.BUY, CoinExClient.OrderSide.SELL]:
            result = await auth_client.get_orders(
                market_type=CoinExClient.MarketType.SPOT,
                side=side,
                status=CoinExClient.OrderStatus.FINISHED,
                limit=3
            )
            
            assert isinstance(result, dict)
            assert "code" in result
            
            # With valid credentials, this should succeed
            assert result["code"] == 0, f"Expected success but got error: {result.get('message', 'Unknown error')}"
            assert "data" in result
            data = result["data"]
            assert isinstance(data, list)
            
            # If there are orders, they should all have the correct side
            for order in data:
                if order and "side" in order:
                    assert order["side"] == side.value


class TestAuthenticationErrors:
    """Test authentication error handling"""

    @pytest.mark.asyncio
    async def test_no_credentials_client(self):
        """Test client without credentials"""
        client = CoinExClient(enable_env_credentials=False)
        
        # Attempting to access authenticated endpoints should raise ValueError
        with pytest.raises(ValueError, match="Account interface requires access_id and secret_key"):
            await client.get_balances(CoinExClient.MarketType.SPOT)

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test client with invalid credentials"""
        client = CoinExClient(
            access_id="invalid_access_id",
            secret_key="invalid_secret_key",
            enable_env_credentials=False
        )
        
        result = await client.get_balances(CoinExClient.MarketType.SPOT)
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # Should get authentication error (including code 4005)
        assert result["code"] in [10013, 10009, 10008, 10012, 4005]
        assert any(keyword in result["message"].lower()
                   for keyword in ["signature", "access", "key", "invalid"])

    @pytest.mark.asyncio
    async def test_invalid_credentials_get_orders(self):
        """Test get_orders with invalid credentials - should fail"""
        client = CoinExClient(
            access_id="invalid_access_id",
            secret_key="invalid_secret_key",
            enable_env_credentials=False
        )
        
        result = await client.get_orders(
            "BTC", "USDT",
            CoinExClient.MarketType.SPOT,
            status=CoinExClient.OrderStatus.FINISHED,
            limit=5
        )
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # Should get authentication error
        assert result["code"] in [10013, 10009, 10008, 10012, 4005]
        assert any(keyword in result["message"].lower()
                   for keyword in ["signature", "access", "key", "invalid"])

    @pytest.mark.asyncio
    async def test_invalid_credentials_futures(self):
        """Test futures balances with invalid credentials - should fail"""
        client = CoinExClient(
            access_id="invalid_access_id",
            secret_key="invalid_secret_key",
            enable_env_credentials=False
        )
        
        result = await client.get_balances(CoinExClient.MarketType.FUTURES)
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # Should get authentication error
        assert result["code"] in [10013, 10009, 10008, 10012, 4005]
        assert any(keyword in result["message"].lower()
                   for keyword in ["signature", "access", "key", "invalid"])


class TestTradingOperationsSafety:
    """Test trading operations safety measures"""

    @pytest.mark.asyncio
    async def test_place_order_dry_run(self, auth_client: CoinExClient, has_auth_credentials):
        """Test place order structure (without actually placing orders)"""
        if not has_auth_credentials:
            pytest.skip("Skipping trading test - no API credentials provided")
        
        # We won't actually place orders to avoid real money transactions
        # Instead, we'll test with invalid parameters to see error handling
        
        # Test with invalid amount (should fail safely)
        result = await auth_client.place_order(
            side=CoinExClient.OrderSide.BUY,
            base="BTC",
            quote="USDT", 
            amount="0",  # Invalid amount
            market_type=CoinExClient.MarketType.SPOT,
            price="50000"  # Limit order
        )
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # Should get parameter error for invalid amount
        assert result["code"] == 4004  # amount should be greater than 0
        assert result["message"] == 'invalid argument'

    @pytest.mark.asyncio
    async def test_cancel_order_nonexistent(self, auth_client: CoinExClient, has_auth_credentials):
        """Test canceling non-existent order"""
        if not has_auth_credentials:
            pytest.skip("Skipping trading test - no API credentials provided")
        
        # Try to cancel a non-existent order
        result = await auth_client.cancel_order(
            "BTC", "USDT",
            CoinExClient.MarketType.SPOT,
            order_id=999999999  # Non-existent order ID
        )
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "message" in result
        
        # Should get error for non-existent order
        assert result["code"] == 3600
        assert result["message"] == 'Order not found'

