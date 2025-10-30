# CoinEx MCP Server

[中文版本](README_cn.md) | English

A CoinEx MCP (Model Context Protocol) server that enables AI agents to interact with the CoinEx cryptocurrency exchange.

## Features

- 🔍 Retrieve market data (spot/futures with unified parameters)
- 💰 Query account balances (authentication required)
- 📊 Get K-line data (spot/futures)
- 📈 View order book depth (spot/futures)
- 💹 Place orders (authentication required)
- 📋 Query order history (authentication required)
- 📜 Futures-specific: funding rates, premium/basis history, margin tiers, liquidation history, etc.

## Installation & Configuration

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure API Credentials

In the default stdio mode, API credentials are obtained through environment variables, but typically MCP servers are not launched directly from the command line. You can configure credentials in two ways:

#### 2.1 MCP Client Configuration
Through MCP clients like Claude Desktop, CherryStudio, or mcp inspector.

#### 2.2 Local File Configuration
1. Copy the environment variable template file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and fill in your CoinEx API credentials:
```env
COINEX_ACCESS_ID=your_access_id_here
COINEX_SECRET_KEY=your_secret_key_here
```
_Note: In SSE or Streamable HTTP mode, environment variable credentials will be ignored._

### 3. Obtain CoinEx API Credentials

1. Log in to [CoinEx Official Website](https://www.coinex.com/)
2. Go to **User Center** -> **API Management**
3. Create a new API Key
4. Copy the Access ID and Secret Key to your `.env` file

⚠️ **Security Notice**:
- Keep your API credentials safe and do not share them with others
- Set appropriate permissions for your API Key, only enabling necessary functions
- Do not commit the `.env` file to version control systems

## Usage

### Start the Server

```bash
python main.py
```

### Command Line Arguments & Examples (New)

`main.py` now supports command line arguments for switching transport protocols and network configuration:

- `--transport`: Transport protocol, options: `stdio` (default) | `http` (equivalent to `streamable-http`) | `streamable-http` | `sse`
- `--host`: HTTP service bind address (only valid for http/streamable-http mode)
- `--port`: HTTP service port (only valid for http/streamable-http mode)
- `--path`: Endpoint path
  - http/streamable-http mode: MCP endpoint path (default `/mcp`)
  - sse mode: SSE mount path
- `--enable-http-auth`: Enable HTTP-based authentication and sensitive tools (disabled by default, only exposes query tools)
- `--workers`: Number of worker processes for HTTP/SSE mode (managed by underlying uvicorn)

#### View Help:
```bash
python main.py --help
```

#### Default stdio Service Start
(Usually no manual start needed, configure startup file and parameters in agent)
```bash
python main.py
```

#### Start HTTP Service
```bash
python main.py --transport http --host 0.0.0.0 --port 8000 --path /mcp --workers 2
```

Note: If using HTTP GET method to directly access the `/mcp` endpoint, it may return `406 Not Acceptable`, which is normal—Streamable HTTP endpoints require protocol-compliant interaction flows; this return code also proves the HTTP service has started and is responding.

### Pass CoinEx Credentials via HTTP Headers (HTTP Mode)
The server does not store third-party exchange credentials. For tools requiring authentication (balance/place order/cancel order/order history), include the following headers in HTTP requests (case-insensitive):
- `X-CoinEx-Access-Id: <your CoinEx Access ID>`
- `X-CoinEx-Secret-Key: <your CoinEx Secret Key>`

**Important Notes**
- **Never** enable credential pass-through functionality in publicly exposed services; ensure the entire server backend is controlled within an internal network! (Even with HTTPS transport, reverse proxies and other server nodes may offload request headers and log them)
- Deploy via HTTPS to prevent man-in-the-middle eavesdropping (use reverse proxy/Nginx/Caddy to add TLS to MCP endpoints).
- These headers are only needed when "HTTP authentication is enabled" and you're calling tools that require user credentials (auth tag).
  - Enable with: `--enable-http-auth` or set environment variable `HTTP_AUTH_ENABLED=true`
  - By default, HTTP authentication is disabled, exposing only query tools (public), which don't need or read the above headers.
- Only valid for HTTP/Streamable HTTP mode; STDIO mode reads credentials from environment variables (or .env config file).

### Logging & Security
- Ensure reverse proxies/APM/logging systems don't record sensitive headers like `Authorization` or `X-CoinEx-*`.

## Tools Overview

Note: In HTTP mode, only `public` type tools are exposed by default; `auth` type tools require enabling `--enable-http-auth` or setting `HTTP_AUTH_ENABLED=true` to be available.

### Standard Parameter Conventions:
- `market_type`: Default `"spot"`, use `"futures"` for contracts.
- `symbol`: Supports `BTCUSDT` / `BTC/USDT` / `btc` / `BTC` (defaults to `USDT` if no quote currency).
- `interval` (depth aggregation levels): Default `"0"`.
- `period`: Default `"1hour"`, validated against spot/futures whitelists.
- `start_time`/`end_time`: Millisecond timestamps.

### Market Data (public)
* `list_markets(market_type="spot"|"futures", symbols: str|list[str]|None)`
  - Get market status; `symbols` can be comma-separated or array, returns all if not provided.
* `get_tickers(market_type="spot"|"futures", symbol: str|list[str]|None, top_n=5)`
  - Get ticker snapshots; returns top `top_n` when `symbol` not provided.
* `get_orderbook(symbol, limit=20, market_type="spot"|"futures", interval="0")`
  - Get order book (depth); supports futures.
* `get_kline(symbol, period="1hour", limit=100, market_type="spot"|"futures")`
  - Get K-line data; periods validated against respective spot/futures whitelists.
* `get_recent_trades(symbol, market_type="spot"|"futures", limit=100)`
  - Get recent trades (deals).
* `get_index_price(market_type="spot"|"futures", symbol: str|list[str]|None, top_n=5)`
  - Get market index (spot/futures).

### Futures-Specific (public)
* `get_funding_rate(symbol)`
  - Get current funding rate.
* `get_funding_rate_history(symbol, start_time?, end_time?, page=1, limit=100)`
  - Get funding rate history.
* `get_premium_index_history(symbol, start_time?, end_time?, page=1, limit=100)`
  - Get premium index history.
* `get_basis_history(symbol, start_time?, end_time?, page=1, limit=100)`
  - Get basis rate history.
* `get_position_tiers(symbol)`
  - Get position tiers/margin tier information.
* `get_liquidation_history(symbol?, side?, start_time?, end_time?, page=1, limit=100)`
  - Get liquidation history.

### Account & Trading (auth)
* `get_account_balance()`
  - Get account balance information.
* `place_order(symbol, side, type, amount, price?)`
  - Place trading order.
* `cancel_order(symbol, order_id)`
  - Cancel order.
* `get_order_history(symbol?, limit=100)`
  - Get order history (open orders + completed orders).

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `COINEX_ACCESS_ID` | CoinEx API Access ID | No (optional with HTTP pass-through) |
| `COINEX_SECRET_KEY` | CoinEx API Secret Key | No (optional with HTTP pass-through) |
| `API_TOKEN` | Bearer token to protect MCP endpoint | No |
| `API_SCOPES` | Required scopes for endpoint | No |
| `HTTP_AUTH_ENABLED` | Enable HTTP authentication (default false) | No |

## Development

### Project Structure

```
coinex_mcp_server/
├── main.py              # MCP server main file
├── coinex_client.py     # CoinEx API client (unified spot/futures wrapper)
├── doc/
│   ├── coinex_api/      
│   │   └── coinex_api.md # CoinEx API documentation
├── pyproject.toml       # Project configuration
└── README.md           # Project documentation
```

### Dependencies

- `fastmcp` - FastMCP framework (2.x)
- `httpx` - HTTP client
- `python-dotenv` - Environment variable loading

## Troubleshooting
- If calls return `code != 0`, record the `message` and check parameters (`period`, `limit`, `symbol` normalization).
- In corporate network environments or with firewall restrictions, external APIs may be blocked; please verify network policies.

## License

This project is open source under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) license.

## Contributing
Issues and Pull Requests are welcome!

## Disclaimer
This tool is for educational and research purposes only. When using this tool for actual trading, please fully understand the risks and operate carefully. The developers are not responsible for any losses resulting from the use of this tool.
