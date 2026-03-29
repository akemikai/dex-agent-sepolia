# DEX Agent — Sepolia Testnet + Stabilizer

**Auto-trading bot for Sepolia Testnet with Stabilizer DEX**

## Description
Direct DEX swap execution on Sepolia testnet via Stabilizer. 
For testing purposes only - no real funds.

## When to Use
- User wants to test auto-trading on testnet
- User wants to swap USDC/USDT/USDZ on Stabilizer
- Development and testing of trading strategies

## Setup
1. Install dependencies: `pip3 install web3 eth-abi`
2. Generate a wallet: `python3 wallet.py generate`
3. Fund the wallet with ETH (gas) and tokens on Sepolia
4. Start trading!

```bash
cd /root/.openclaw/workspace/skills/dex-agent-sepolia/scripts
pip3 install web3 eth-abi
python3 wallet.py generate
```

## Commands

### Check Balance
```bash
python3 wallet.py balance
```

### Swap Tokens
```bash
# Swap 5 USDC to USDT
python3 swap.py USDC USDT 5

# Swap 1 USDZ to USDC  
python3 swap.py USDZ USDC 1
```

### Price Quote
```bash
python3 quote.py USDC USDT 5
```

## Tokens Available (Sepolia)
- USDC: 0x77ef087024F87976aAdA0Aa7F73BB8EAe6E9dda1
- USDT: 0xee0418Bd560613fbcF924C36235AB1ec301D4933
- USDZ: 0x55Cc481D28Db3f1ffc9347745AA6fbB940505BdD
- WETH: 0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9

## Router
- Stabilizer Router: 0xfa6419a3d3503a016df3a59f690734862ca2a78d

## Warning
⚠️ This is for TESTNET ONLY. Do not use with real funds!