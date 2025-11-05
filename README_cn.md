# CoinEx MCP Server

[English](README.md) | 中文版本

CoinEx MCP（Model Context Protocol）服务器，用于让 ai agent 拥有访问 CoinEx 加密货币交易所的能力。

## 功能特性

- 🔍 获取市场行情数据（现货/合约，统一参数）
- 💰 查询账户余额（需认证）
- 📊 获取 K 线数据（现货/合约）
- 📈 查看交易深度（现货/合约）
- 💹 下单交易（需认证）
- 📋 查询订单历史（需认证）
- 📜 合约专属：资金费率、溢价/基差历史、仓位阶梯、强平历史等等

## 安装与配置

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置 API 凭证
在缺省的 stdio 模式中，API 凭证是通过环境变量获取的，但通常 MCP Server 并不会直接从命令行启动。 可以通过以下两种方式配置：

#### 2.1 基于 MCP 客户端配置
比如 Claude Desktop、CherryStudio 或者 mcp inspector 等。

#### 2.2 基于本地文件配置
1. 复制环境变量模板文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的 CoinEx API 凭证：
```env
COINEX_ACCESS_ID=your_access_id_here
COINEX_SECRET_KEY=your_secret_key_here
```
_注意，如果是 SSE 或者 Streamable HTTP 模式，环境变量中的凭证将被忽略。

### 3. 获取 CoinEx API 凭证

1. 登录 [CoinEx 官网](https://www.coinex.com/)
2. 进入 **用户中心** -> **API 管理**
3. 创建新的 API Key
4. 复制 Access ID 和 Secret Key 到 `.env` 文件中

⚠️ **安全提示**：
- 请妥善保管您的 API 凭证，不要泄露给他人
- 建议为 API Key 设置合适的权限，只开启必要的功能
- 不要将 `.env` 文件提交到版本控制系统

## MCP 客户端配置

项目已发布到 PyPI，你可以在 MCP 客户端中配置使用此服务器，无需预先安装包。

### 使用 uvx（推荐）

[uvx](https://docs.astral.sh/uv/guides/tools/) 会自动管理包的安装和环境隔离，类似于 Node.js 的 npx。

#### Claude Desktop 配置

编辑 Claude Desktop 配置文件：
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "coinex": {
      "command": "uvx",
      "args": ["coinex-mcp-server"],
      "env": {
        "COINEX_ACCESS_ID": "你的_access_id",
        "COINEX_SECRET_KEY": "你的_secret_key"
      }
    }
  }
}
```

#### CherryStudio 配置

在 CherryStudio 的 MCP 设置中添加：

```json
{
  "mcpServers": {
    "coinex": {
      "command": "uvx",
      "args": ["coinex-mcp-server"],
      "env": {
        "COINEX_ACCESS_ID": "你的_access_id",
        "COINEX_SECRET_KEY": "你的_secret_key"
      }
    }
  }
}
```

#### 使用 uvx 启动 HTTP 模式

如需以 HTTP 模式运行服务器：

```json
{
  "mcpServers": {
    "coinex-http": {
      "command": "uvx",
      "args": [
        "coinex-mcp-server",
        "--transport",
        "http",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--path",
        "/mcp"
      ]
    }
  }
}
```

### 使用预安装的包

如果你希望先安装包：

```bash
# 安装包
pip install coinex-mcp-server

# 或者使用 uv
uv pip install coinex-mcp-server
```

然后配置 MCP 客户端：

```json
{
  "mcpServers": {
    "coinex": {
      "command": "python",
      "args": [
        "-m",
        "coinex_mcp_server.main"
      ],
      "env": {
        "COINEX_ACCESS_ID": "你的_access_id",
        "COINEX_SECRET_KEY": "你的_secret_key"
      }
    }
  }
}
```

## 本地使用方法

### 克隆源码
`git clone https://github.com/coinexcom/coinex_mcp_server`

### 启动服务器

```bash
python -m coinex_mcp_server.main
```

### 启动参数与示例

服务器支持命令行参数，便于切换传输协议与网络配置：

- `--transport`：传输协议，可选 `stdio`（默认）| `http`（等价于 `streamable-http`）| `streamable-http` | `sse`
- `--host`：HTTP 服务绑定地址（仅 http/streamable-http 模式有效）
- `--port`：HTTP 服务端口（仅 http/streamable-http 模式有效）
- `--path`：端点路径
  - http/streamable-http 模式：MCP 端点路径（默认 `/mcp`）
  - sse 模式：SSE 挂载路径
- `--enable-http-auth`：启用基于 HTTP 的认证与敏感工具（默认关闭，仅暴露查询类工具）
- `--workers`：HTTP/SSE 模式下的工作进程数（由底层 uvicorn 管理）

#### 查看帮助：
```bash
python -m coinex_mcp_server.main --help
```
#### 缺省启动 stdio 服务
（通常不需要手工启动，在 agent 中配置启动文件和参数即可）
```bash
python -m coinex_mcp_server.main
```

#### 启动 HTTP 服务
```bash
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000 --path /mcp --workers 2
```

说明：若使用 HTTP GET 方法直接访问 `/mcp` 端点，可能返回 `406 Not Acceptable`，这是正常的——Streamable HTTP 端点需要符合协议的交互流程；该返回码也可证明 HTTP 服务已启动并在响应。

### 通过请求头透传 CoinEx 凭证（HTTP 模式）
服务端不保存第三方交易所凭证。对于需要认证的工具（余额/下单/撤单/订单历史），请在 HTTP 请求中携带以下请求头（大小写不敏感）：
- `X-CoinEx-Access-Id: <你的 CoinEx Access ID>`
- `X-CoinEx-Secret-Key: <你的 CoinEx Secret Key>`

**注意事项**
- **一定不要**在对外公开服务中，启用透传凭证功能，要确保整个服务端内网可控！！！（即使采用 HTTPS 传输，在反向代理等服务端节点，有可能卸载请求头，记录日志）
- 建议通过 HTTPS 部署，防止中间人窃听（可用反向代理/Nginx/Caddy 等为 MCP 端点加 TLS）。
- 仅当“已启用 HTTP 认证”且你调用的是需要用户凭证的工具（auth 标签）时才需要这些请求头。
  - 启用方式：`--enable-http-auth` 或设置环境变量 `HTTP_AUTH_ENABLED=true`
  - 默认情况下 HTTP 认证关闭，此时仅暴露查询类工具（public），这些工具不需要也不会读取上述请求头。
- 仅对 HTTP/Streamable HTTP 模式有效；STDIO 模式从环境变量（或者.env 配置文件）读取凭证。

### 日志与安全
- 确保反向代理/APM/日志系统不会记录 `Authorization` 或 `X-CoinEx-*` 这类敏感请求头。

## 工具一览（Tools）

注意：在 HTTP 模式默认仅暴露`public`类型的工具，`auth`类型的需开启 `--enable-http-auth` 或设置 `HTTP_AUTH_ENABLED=true` 才会对外可用。

### 标准参数约定：
- `market_type`: 默认 `"spot"`，合约用 `"futures"`。
- `symbol`: 支持 `BTCUSDT` / `BTC/USDT` / `btc` / `BTC`（未带计价币默认补 `USDT`）。
- `interval`（深度档位）：默认 `"0"`。
- `period`：默认 `"1hour"`，按现货/合约白名单校验。
- `start_time`/`end_time`：毫秒时间戳。

### 市场数据（public）
* `list_markets(market_type="spot"|"futures", symbols: str|list[str]|None)`
  - 获取市场状态；`symbols` 可传逗号分隔或数组，不传返回全部。
* `get_tickers(market_type="spot"|"futures", symbol: str|list[str]|None, top_n=5)`
  - 获取行情快照；不传 `symbol` 时返回前 `top_n` 条。
* `get_orderbook(symbol, limit=20, market_type="spot"|"futures", interval="0")`
  - 获取订单簿（深度）；支持合约。
* `get_kline(symbol, period="1hour", limit=100, market_type="spot"|"futures")`
  - 获取 K 线；周期会按现货/合约各自白名单校验。
* `get_recent_trades(symbol, market_type="spot"|"futures", limit=100)`
  - 获取最近成交（deals）。
* `get_index_price(market_type="spot"|"futures", symbol: str|list[str]|None, top_n=5)`
  - 获取市场指数（现货/合约）。

### 合约专属（public）
* `get_funding_rate(symbol)`
  - 获取当前资金费率。
* `get_funding_rate_history(symbol, start_time?, end_time?, page=1, limit=100)`
  - 获取资金费率历史。
* `get_premium_index_history(symbol, start_time?, end_time?, page=1, limit=100)`
  - 获取溢价指数历史。
* `get_basis_history(symbol, start_time?, end_time?, page=1, limit=100)`
  - 获取基差率历史。
* `get_position_tiers(symbol)`
  - 获取仓位阶梯/保证金分层信息。
* `get_liquidation_history(symbol?, side?, start_time?, end_time?, page=1, limit=100)`
  - 获取强平历史。

### 账户与交易（auth）
* `get_account_balance()`
  - 获取账户余额信息。
* `place_order(symbol, side, type, amount, price?)`
  - 下单交易。
* `cancel_order(symbol, order_id)`
  - 取消订单。
* `get_order_history(symbol?, limit=100)`
  - 获取订单历史（当前挂单 + 已完成订单）。

## 环境变量说明

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `COINEX_ACCESS_ID` | CoinEx API Access ID | 否（HTTP 透传时可不设） |
| `COINEX_SECRET_KEY` | CoinEx API Secret Key | 否（HTTP 透传时可不设） |
| `API_TOKEN` | 保护 MCP 端点的 Bearer 令牌 | 否 |
| `API_SCOPES` | 端点所需 scopes | 否 |
| `HTTP_AUTH_ENABLED` | 是否启用 HTTP 认证（默认 false） | 否 |

## 开发

### 项目结构

```
coinex_mcp_server/
├── main.py              # MCP 服务器主文件
├── coinex_client.py     # CoinEx API 客户端（统一封装现货/合约差异）
├── doc/
│   ├── coinex_api/      
│   │   └── coinex_api.md # CoinEx API 文档
├── pyproject.toml       # 项目配置
└── README.md           # 项目说明
```

### 依赖项

- `fastmcp` - FastMCP 框架（2.x）
- `httpx` - HTTP 客户端
- `python-dotenv` - 环境变量加载

## 故障排除
- 若调用出现 `code != 0`，请记录 `message` 并检查传参（`period`、`limit`、`symbol` 归一）。
- 若在公司网络环境或防火墙限制下，外部 API 可能被阻断，请确认网络策略。

## 许可证

本项目基于 [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) 许可证开源。

## 贡献
欢迎提交 Issue 和 Pull Request！

## 免责声明
本工具仅供学习和研究使用。使用本工具进行实际交易时，请充分了解风险并谨慎操作。开发者不承担任何因使用本工具而产生的损失。
