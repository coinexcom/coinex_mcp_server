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

## 快速开始

根据您的需求选择以下安装方式之一：

1. **在线 HTTP 服务**（推荐）- 无需本地安装，仅支持公开市场数据查询
2. **本地安装（uvx/pip）** - 支持认证操作（余额查询、交易下单）
3. **源码安装** - 用于开发或自定义

### 获取 CoinEx API 凭证（可选）

API 凭证仅在需要认证操作（账户余额、交易下单）时必需。如果只需要查询市场数据，可以跳过此步骤。

1. 登录 [CoinEx 官网](https://www.coinex.com/)
2. 进入 **用户中心** -> **API 管理**
3. 创建新的 API Key
4. 复制 Access ID 和 Secret Key 备用

⚠️ **安全提示**：
- 请妥善保管您的 API 凭证，不要泄露给他人
- 建议为 API Key 设置合适的权限，只开启必要的功能
- 不要将凭证提交到版本控制系统

---

## 安装方式 1：在线 HTTP 服务（推荐）

**无需本地安装。** 使用 CoinEx 托管的 MCP 服务：`https://mcp.coinex.com/mcp`

⚠️ **注意**：在线服务仅提供公开市场数据查询。如需认证操作（余额、交易），请使用方式 2 或 3。

### Claude Code

```bash
claude mcp add --transport http coinex-mcp-server https://mcp.coinex.com/mcp
```

### Claude Desktop

编辑 Claude Desktop 配置文件：
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

在 CherryStudio 的 MCP GUI 设置中添加：

<img src="images/CherryStudio_HTTP.png"  alt="CherryStudio CoinEx MCP 配置"/>

---

## 安装方式 2：本地安装（uvx/pip）

在本地安装包以支持使用您的 API 凭证进行认证操作。

### 选项 A：使用 uvx（推荐）

无需预先安装，包会自动下载并运行。[uvx](https://docs.astral.sh/uv/guides/tools/) 类似于 Node.js 的 npx。

#### Claude Desktop

编辑 Claude Desktop 配置文件：

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

#### Claude Code

```bash
# 添加服务器
claude mcp add coinex-mcp-server uvx coinex-mcp-server

# 然后手动编辑配置文件添加环境变量
# 配置文件位置: ~/.config/claude/config.json
# 在 coinex-mcp-server 配置中添加 env 字段：
# "env": {
#   "COINEX_ACCESS_ID": "你的_access_id",
#   "COINEX_SECRET_KEY": "你的_secret_key"
# }
```

#### CherryStudio

在 CherryStudio 的 MCP GUI 设置中添加：

<img src="images/CherryStudio_uvx.png"  alt="CherryStudio CoinEx MCP 配置"/>

### 选项 B：使用 pip 安装

首先安装包：

```bash
# 使用 pip
pip install coinex-mcp-server

# 或使用 uv
uv pip install coinex-mcp-server
```

然后配置 MCP 客户端：

#### Claude Desktop

```json
{
  "mcpServers": {
    "coinex": {
      "command": "python",
      "args": ["-m", "coinex_mcp_server.main"],
      "env": {
        "COINEX_ACCESS_ID": "你的_access_id",
        "COINEX_SECRET_KEY": "你的_secret_key"
      }
    }
  }
}
```

#### Claude Code

```bash
# 添加服务器
claude mcp add coinex-mcp-server python -m coinex_mcp_server.main

# 然后手动编辑配置文件添加环境变量
# 配置文件位置: ~/.config/claude/config.json
# 在 coinex-mcp-server 配置中添加 env 字段：
# "env": {
#   "COINEX_ACCESS_ID": "你的_access_id",
#   "COINEX_SECRET_KEY": "你的_secret_key"
# }
```

#### CherryStudio

<img src="images/CherryStudio_python.png"  alt="CherryStudio CoinEx MCP 配置"/>

---

## 安装方式 3：源码安装

用于开发或自定义需求。

### 步骤 1：克隆仓库

```bash
git clone https://github.com/coinexcom/coinex_mcp_server
cd coinex_mcp_server
```

### 步骤 2：安装依赖

```bash
uv sync
```

### 步骤 3：配置 API 凭证

复制环境变量模板文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 CoinEx API 凭证：

```env
COINEX_ACCESS_ID=你的_access_id
COINEX_SECRET_KEY=你的_secret_key
```

### 步骤 4：配置 MCP 客户端

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
# 从项目目录运行
cd /path/to/coinex_mcp_server
python -m coinex_mcp_server.main
```

#### CherryStudio

<img src="images/CherryStudio_python.png"  alt="CherryStudio CoinEx MCP 配置"/>


### 步骤 5：运行服务器（可选）

用于测试或以本地服务运行：

```bash
# 默认 stdio 模式
python -m coinex_mcp_server.main

# HTTP 模式
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000

# 查看所有可用选项
python -m coinex_mcp_server.main --help
```

---

## 高级配置

### 命令行参数

服务器支持以下命令行参数：

- `--transport`：传输协议
  - 可选：`stdio`（默认）| `http` | `streamable-http` | `sse`
- `--host`：HTTP 服务绑定地址（仅 HTTP/SSE 模式）
  - 默认：`127.0.0.1`
- `--port`：HTTP 服务端口（仅 HTTP/SSE 模式）
  - 默认：`8000`
- `--path`：端点路径
  - HTTP 模式：MCP 端点路径（默认 `/mcp`）
  - SSE 模式：SSE 挂载路径
- `--enable-http-auth`：启用基于 HTTP 的认证与交易工具
  - 默认：`false`（仅暴露公开市场数据工具）
- `--workers`：工作进程数（仅 HTTP/SSE 模式）

### 以 HTTP 服务方式运行

```bash
# 基础 HTTP 服务
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000

# 启用认证的 HTTP 服务
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000 --enable-http-auth

# 多进程 HTTP 服务
python -m coinex_mcp_server.main --transport http --host 0.0.0.0 --port 8000 --workers 4
```

⚠️ **注意**：若使用 HTTP GET 方法直接访问 `/mcp` 端点，可能返回 `406 Not Acceptable`。这是正常的——Streamable HTTP 端点需要符合协议的交互流程。

### HTTP 认证模式

在 HTTP 模式下使用 `--enable-http-auth` 时，可以通过 HTTP 请求头传递 CoinEx 凭证：

**请求头：**
- `X-CoinEx-Access-Id`：您的 CoinEx Access ID
- `X-CoinEx-Secret-Key`：您的 CoinEx Secret Key

**安全注意事项：**
- **一定不要**在对外公开的服务中启用 HTTP 认证
- 生产环境必须使用 HTTPS（使用 Nginx/Caddy 等反向代理）
- 确保反向代理/APM/日志系统不记录敏感请求头
- 仅在可信的内网环境中使用
- 默认情况下，HTTP 模式仅暴露公开市场数据工具（无需认证）

---

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
