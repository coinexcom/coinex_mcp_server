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

## Quick Start

Choose one of the following installation methods based on your needs:

1. **Online HTTP Service** (Recommended) - No local installation required, public market data only
2. **Local Installation via uvx/pip** - Supports authenticated operations (balance queries, trading)
3. **From Source** - For development or customization

### Obtaining CoinEx API Credentials (Optional)

API credentials are only required for authenticated operations (account balance, trading). For market data queries only, you can skip this step.

1. Log in to [CoinEx Official Website](https://www.coinex.com/)
2. Go to **User Center** -> **API Management**
3. Create a new API Key
4. Copy the Access ID and Secret Key for later use

⚠️ **Security Notice**:
- Keep your API credentials safe and do not share them with others
- Set appropriate permissions for your API Key, only enabling necessary functions
- Do not commit credentials to version control systems

---

## Installation Method 1: Online HTTP Service (Recommended)

**No local installation required.** Use CoinEx's hosted MCP service at `https://mcp.coinex.com/mcp`.

⚠️ **Note**: The online service only provides public market data queries. For authenticated operations (balance, trading), use Method 2 or 3.

### Claude Code

```bash
claude mcp add --transport http coinex-mcp-server https://mcp.coinex.com/mcp
```

### Claude Desktop

Edit your Claude Desktop configuration file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "coinex": {
      "command": "http",
      "args": ["https://mcp.coinex.com/mcp"]
    }
  }
}
```

### CherryStudio

In CherryStudio's MCP settings, GUI configuration:

<img src="images/CherryStudio_HTTP_en.png"  alt="CherryStudio CoinEx MCP Configuration"/>

---

## Installation Method 2: Local Installation via uvx/pip

Install the package locally to support authenticated operations with your API credentials.

### Option A: Using uvx (Recommended)

No pre-installation needed. The package will be automatically downloaded and run.

#### Claude Desktop

Edit your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "coinex": {
      "command": "uvx",
      "args": ["coinex-mcp-server"],
      "env": {
        "COINEX_ACCESS_ID": "your_access_id_here",
        "COINEX_SECRET_KEY": "your_secret_key_here"
      }
    }
  }
}
```

#### Claude Code

```bash
# Add the server
claude mcp add coinex-mcp-server uvx coinex-mcp-server

# Then manually edit the config file to add environment variables
# Config file location: ~/.config/claude/config.json
# Add env field to the coinex-mcp-server configuration:
# "env": {
#   "COINEX_ACCESS_ID": "your_access_id",
#   "COINEX_SECRET_KEY": "your_secret_key"
# }
```

#### CherryStudio

In CherryStudio's MCP settings, add:

<img src="images/CherryStudio_uvx_en.png"  alt="CherryStudio CoinEx MCP Configuration"/>

### Option B: Using pip install

First, install the package:

```bash
# Using pip
pip install coinex-mcp-server

# Or using uv
uv pip install coinex-mcp-server
```

Then configure your MCP client:

#### Claude Desktop

```json
{
  "mcpServers": {
    "coinex": {
      "command": "python",
      "args": ["-m", "coinex_mcp_server.main"],
      "env": {
        "COINEX_ACCESS_ID": "your_access_id_here",
        "COINEX_SECRET_KEY": "your_secret_key_here"
      }
    }
  }
}
```

#### Claude Code

```bash
# Add the server
claude mcp add coinex-mcp-server python -m coinex_mcp_server.main

# Then manually edit the config file to add environment variables
# Config file location: ~/.config/claude/config.json
# Add env field to the coinex-mcp-server configuration:
# "env": {
#   "COINEX_ACCESS_ID": "your_access_id",
#   "COINEX_SECRET_KEY": "your_secret_key"
# }
```

#### CherryStudio

<img src="images/CherryStudio_python_en.png"  alt="CherryStudio CoinEx MCP Configuration"/>

---

## Installation Method 3: From Source

For development or customization purposes.

### Step 1: Clone the Repository

```bash
git clone https://github.com/coinexcom/coinex_mcp_server
cd coinex_mcp_server
```

### Step 2: Install Dependencies

```bash
uv sync
```

### Step 3: Configure API Credentials

Copy the environment variable template file:

```bash
cp .env.example .env
```

Edit the `.env` file and fill in your CoinEx API credentials:

```env
COINEX_ACCESS_ID=your_access_id_here
COINEX_SECRET_KEY=your_secret_key_here
```

### Step 4: Configure MCP Client

#### Claude Desktop

```json
{
  "mcpServers": {
    "coinex": {
      "command": "python",
      "args": ["-m", "coinex_mcp_server.main"],
      "cwd": "/path/to/coinex_mcp_server/src"
    }
  }
}
```

#### Claude Code

```bash
# Run from the project directory
cd /path/to/coinex_mcp_server
python -m coinex_mcp_server.main
```

#### CherryStudio

<img src="images/CherryStudio_python_en.png"  alt="CherryStudio CoinEx MCP Configuration"/>

### Step 5: Run the Server (Optional)

For testing or running in HTTP mode:

```bash
# Default stdio mode
python -m coinex_mcp_server.main

# HTTP mode
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000

# View all available options
python -m coinex_mcp_server.main --help
```

---

## Advanced Configuration

### Command Line Arguments

The server supports the following command line arguments:

- `--transport`: Transport protocol
  - Options: `stdio` (default) | `http` | `streamable-http` | `sse`
- `--host`: HTTP service bind address (HTTP/SSE mode only)
  - Default: `127.0.0.1`
- `--port`: HTTP service port (HTTP/SSE mode only)
  - Default: `8000`
- `--path`: Endpoint path
  - HTTP mode: MCP endpoint path (default `/mcp`)
  - SSE mode: SSE mount path
- `--enable-http-auth`: Enable HTTP-based authentication for trading tools
  - Default: `false` (only public market data tools exposed)
- `--workers`: Number of worker processes (HTTP/SSE mode only)

### Running as HTTP Service

```bash
# Basic HTTP service
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000

# HTTP service with authentication enabled
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000 --enable-http-auth

# HTTP service with multiple workers
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000 --workers 4
```

⚠️ **Note**: If you access the `/mcp` endpoint directly via HTTP GET, it may return `406 Not Acceptable`. This is normal—Streamable HTTP endpoints require protocol-compliant interaction flows.

### HTTP Authentication Mode

When running in HTTP mode with `--enable-http-auth`, you can pass CoinEx credentials via HTTP headers:

**Request Headers:**
- `X-CoinEx-Access-Id`: Your CoinEx Access ID
- `X-CoinEx-Secret-Key`: Your CoinEx Secret Key

**Security Considerations:**
- **Never** enable HTTP authentication on publicly exposed services
- Always use HTTPS in production (use reverse proxy like Nginx/Caddy)
- Ensure reverse proxies/APM/logging systems don't record sensitive headers
- Only use in trusted internal network environments
- By default, HTTP mode only exposes public market data tools (no authentication required)

---

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
