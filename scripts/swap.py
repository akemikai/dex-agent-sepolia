"""
DEX Agent — Sepolia + Stabilizer (Python)
With .env config
"""

import os
import sys
from pathlib import Path
from web3 import Web3

# Load .env
ENV_FILE = Path(__file__).parent / ".env"

def load_env():
    env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip()
    return env

env = load_env()

# Config from .env
PRIVATE_KEY = env.get('PRIVATE_KEY', '')
RPC_URL = env.get('RPC_URL', 'https://sepolia.infura.io/v3/84842078b09946638c03157f83405213')
CHAIN_ID = 11155111

# Tokens (checksum address)
TOKENS = {
    "USDC": Web3.to_checksum_address("0x77ef087024F87976aAdA0Aa7F73BB8EAe6E9dda1"),
    "USDT": Web3.to_checksum_address("0xee0418Bd560613fbcF924C36235AB1ec301D4933"),
    "USDZ": Web3.to_checksum_address("0x55Cc481D28Db3f1ffc9347745AA6fbB940505BdD"),
}

ROUTER = Web3.to_checksum_address("0xfa6419a3d3503a016df3a59f690734862ca2a78d")

# ABIs
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

STABILIZER_ROUTER_ABI = [
    {"inputs": [
        {"name": "fromToken", "type": "address"},
        {"name": "toToken", "type": "address"},
        {"name": "amount", "type": "uint256"},
        {"name": "minReceive", "type": "uint256"}
    ], "name": "swap", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "nonpayable", "type": "function"}
]

def main():
    if not PRIVATE_KEY:
        print("❌ PRIVATE_KEY not set in .env")
        return
    
    if len(sys.argv) < 4:
        print("Usage: python3 swap.py <from_token> <to_token> <amount>")
        print("Example: python3 swap.py USDC USDT 5")
        print("\nCreate .env file with:")
        print("PRIVATE_KEY=0x...")
        return
    
    from_token = sys.argv[1].upper()
    to_token = sys.argv[2].upper()
    amount_str = sys.argv[3]
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ Cannot connect to RPC")
        return
    
    print(f"✅ Connected to Sepolia (block: {w3.eth.block_number})")
    
    # Get account
    account = w3.eth.account.from_key(PRIVATE_KEY)
    wallet_addr = Web3.to_checksum_address(account.address)
    
    from_addr = TOKENS.get(from_token)
    to_addr = TOKENS.get(to_token)
    
    if not from_addr or not to_addr:
        print(f"❌ Unknown token: {from_token} or {to_token}")
        print(f"Available: {list(TOKENS.keys())}")
        return
    
    # Amount in wei (18 decimals for Stabilizer)
    amount_wei = w3.to_wei(amount_str, 'ether')
    
    # Check balance
    token = w3.eth.contract(address=from_addr, abi=ERC20_ABI)
    balance = token.functions.balanceOf(wallet_addr).call()
    balance_eth = w3.from_wei(balance, 'ether')
    
    print(f"\n🔄 Swap: {amount_str} {from_token} → {to_token}")
    print(f"👛 Wallet: {wallet_addr}")
    print(f"💰 Balance: {balance_eth} {from_token}")
    
    if balance < amount_wei:
        print(f"❌ Insufficient balance!")
        return
    
    # Check & approve
    allowance = token.functions.allowance(wallet_addr, ROUTER).call()
    if allowance < amount_wei:
        print(f"⏳ Approving {from_token}...")
        nonce = w3.eth.get_transaction_count(wallet_addr)
        approve_tx = token.functions.approve(ROUTER, 2**256 - 1).build_transaction({
            'from': wallet_addr, 'nonce': nonce, 'gas': 100000,
            'gasPrice': w3.eth.gas_price, 'chainId': CHAIN_ID
        })
        signed = w3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"✅ Approved!")
    
    # Swap
    min_receive = amount_wei * 99 // 100  # 1% slippage
    
    router = w3.eth.contract(address=ROUTER, abi=STABILIZER_ROUTER_ABI)
    
    try:
        nonce = w3.eth.get_transaction_count(wallet_addr)
        swap_tx = router.functions.swap(from_addr, to_addr, amount_wei, min_receive).build_transaction({
            'from': wallet_addr, 'nonce': nonce, 'gas': 300000,
            'gasPrice': w3.eth.gas_price, 'chainId': CHAIN_ID
        })
        
        print(f"⏳ Sending swap transaction...")
        signed = w3.eth.account.sign_transaction(swap_tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        print(f"📝 Tx: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Swap successful! Gas: {receipt.gasUsed}")
        else:
            print(f"❌ Swap failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()