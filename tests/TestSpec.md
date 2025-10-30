# CoinEx MCP Server Test Suite

This directory contains comprehensive test cases for the CoinEx MCP Server using pytest framework.

## Test Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                # Pytest configuration and fixtures
├── test_spot_market_data.py   # Spot market data API tests
├── test_futures_market_data.py # Futures market data API tests  
├── test_error_handling.py     # Error handling and edge cases
├── test_authentication.py     # Authentication-required features
├── test_main_tools.py         # MCP tools logic tests
└── README.md                  # This file
```

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
uv sync  # This will install pytest and other dev dependencies
```

2. For authentication tests, set environment variables:
```bash
export COINEX_ACCESS_ID=your_access_id
export COINEX_SECRET_KEY=your_secret_key
```

### Basic Test Commands

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_spot_market_data.py

# Run specific test class
pytest tests/test_spot_market_data.py::TestSpotMarketData

# Run specific test method
pytest tests/test_spot_market_data.py::TestSpotMarketData::test_get_tickers_single

# Run tests matching a pattern
pytest -k "test_ticker"

# Run tests with coverage
pytest --cov=coinex_client --cov-report=html

# Run only fast tests (skip slow ones)
pytest -m "not slow"

# Run with different verbosity levels
pytest -q          # Quiet
pytest -v          # Verbose  
pytest -vv         # Very verbose
```

### Test Categories

#### Public API Tests (No Authentication Required)
- `test_spot_market_data.py` - Tests all spot market data endpoints
- `test_futures_market_data.py` - Tests futures market data and futures-specific features
- `test_error_handling.py` - Tests error conditions and edge cases

#### Authentication Required Tests  
- `test_authentication.py` - Tests balance, orders, and trading features
- **Note**: These tests are automatically skipped if no API credentials are provided

#### Logic Tests
- `test_main_tools.py` - Tests the logic behind MCP tools

### Test Features

#### Comprehensive Assertions
All tests include detailed assertions for:
- Response structure validation
- Data type checking
- Value range validation
- Required field verification
- Error code validation

#### Parametrized Tests
Many tests use pytest parametrization to test multiple scenarios:
- Different currency pairs (BTC/USDT, ETH/USDT, LTC/USDT)
- Different market types (spot, futures)
- Different time periods for K-lines
- Different limit values

#### Fixtures
- `public_client` - CoinEx client for public API testing
- `auth_client` - CoinEx client with authentication
- `has_auth_credentials` - Boolean indicating if auth credentials are available
- `currency_pair` - Parametrized currency pairs
- `market_type` - Parametrized market types

#### Safe Testing
- Authentication tests are automatically skipped without credentials
- Trading operations use invalid parameters to avoid real money transactions
- Error conditions are tested safely

## Test Examples

### Successful Test Output
```
tests/test_spot_market_data.py::TestSpotMarketData::test_get_tickers_single[currency_pair0] PASSED
tests/test_spot_market_data.py::TestSpotMarketData::test_get_depth PASSED
tests/test_futures_market_data.py::TestFuturesSpecificFeatures::test_get_funding_rate PASSED
```

### Error Test Output  
```
tests/test_error_handling.py::TestErrorHandling::test_invalid_currency_pair PASSED
tests/test_error_handling.py::TestErrorHandling::test_invalid_kline_period PASSED
```

### Skipped Authentication Tests
```
tests/test_authentication.py::TestAuthenticationRequired::test_get_balances_spot SKIPPED (no API credentials)
```

## Writing New Tests

### Test Structure Template
```python
import pytest
from coinex_client import CoinExClient

class TestNewFeature:
    """Test description"""

    @pytest.mark.asyncio
    async def test_feature_name(self, public_client: CoinExClient):
        """Test specific feature"""
        result = await public_client.some_method("BTC", "USDT")
        
        # Basic structure assertions
        assert isinstance(result, dict)
        assert result["code"] == 0
        assert result["message"] == "OK"
        assert "data" in result
        
        # Data content assertions
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Field validation
        item = data[0]
        assert "required_field" in item
        assert isinstance(item["required_field"], str)
```

### Best Practices

1. **Always test response structure** - Check for required fields and data types
2. **Test both success and error cases** - Include invalid parameters
3. **Use parametrized tests** - Test multiple scenarios efficiently  
4. **Add descriptive assertions** - Use helpful error messages
5. **Test edge cases** - Empty responses, boundary values, etc.
6. **Keep tests independent** - Each test should work in isolation
7. **Use appropriate fixtures** - Public vs auth client based on test needs

## Continuous Integration

These tests are designed to run in CI/CD environments:
- Public API tests will always run
- Authentication tests are safely skipped without credentials
- All tests have reasonable timeouts
- Error conditions are handled gracefully

## Troubleshooting

### Common Issues

1. **Connection timeouts** - Check network connectivity to CoinEx API
2. **Authentication failures** - Verify API credentials are correct
3. **Rate limiting** - CoinEx may have rate limits, consider adding delays
4. **Market unavailability** - Some test markets might be temporarily unavailable

### Debug Mode
```bash
# Run with maximum verbosity and stop on first failure  
pytest -vv -x --tb=long

# Run specific failing test with full output
pytest -vv -s tests/test_spot_market_data.py::TestSpotMarketData::test_get_tickers_single
```