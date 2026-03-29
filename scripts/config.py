"""
DEX Agent Configuration — Sepolia Testnet + Stabilizer DEX
Modified for Sepolia testnet with Stabilizer DEX
"""

# Sepolia Chain
CHAIN_ID = 11155111
RPC_URL = "https://sepolia.infura.io/v3/84842078b09946638c03157f83405213"
BACKUP_RPC = "https://rpc.ankr.com/eth_sepolia"

# Sepolia Testnet Tokens (18 decimals for Stabilizer)
TOKENS = {
    "USDC": "0x77ef087024F87976aAdA0Aa7F73BB8EAe6E9dda1",
    "USDT": "0xee0418Bd560613fbcF924C36235AB1ec301D4933",
    "USDZ": "0x55Cc481D28Db3f1ffc9347745AA6fbB940505BdD",
    "WETH": "0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9",  # Sepolia WETH
}

# Stabilizer Router (Sepolia)
ROUTER = "0xfa6419a3d3503a016df3a59f690734862ca2a78d"

# Trading Parameters (Sepolia = cheaper gas)
DEFAULT_SLIPPAGE_BPS = 100  # 1% default slippage
MAX_SLIPPAGE_BPS = 500      # 5% max slippage
GAS_LIMIT = 300_000

# Risk Management Defaults
RISK_DEFAULTS = {
    "max_daily_trades": 100,      # Max new trades per 24h period
    "max_active_positions": 10,   # Max concurrent open positions
    "trade_size_usd": 5,          # Default trade size in USD (testnet friendly)
    "take_profit_pct": 2.0,       # Take profit trigger (%)
    "stop_loss_pct": 5.0,         # Stop loss trigger (%)
    "max_drawdown_pct": 20.0,     # Max portfolio drawdown before halt
    "cooldown_minutes": 10,       # Min time between trades on same token (testnet = faster)
    "min_liquidity": 1000,        # Min pool liquidity (USD) - lower for testnet
    "min_volume_24h": 5000,       # Min 24h volume (USD) - lower for testnet
}

# Fee Collection Wallet
FEE_WALLET = None