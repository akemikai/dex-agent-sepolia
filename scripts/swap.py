"""
DEX Swap Engine — Stabilizer DEX on Sepolia Testnet
Supports: exact input swaps, slippage protection
"""

import json
import sys
from web3 import Web3

from config import (
    CHAIN_ID, TOKENS, ROUTER,
    DEFAULT_SLIPPAGE_BPS, MAX_SLIPPAGE_BPS, GAS_LIMIT
)
from wallet import load_wallet
from rpc import get_w3

# ABIs
ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol",
     "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
]

# Stabilizer Router ABI (simple swap)
STABILIZER_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "fromToken", "type": "address"},
            {"name": "toToken", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "minReceive", "type": "uint256"}
        ],
        "name": "swap",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def approve_token(w3, token_addr, wallet_addr, private_key, router_addr, amount):
    """Approve token for router"""
    token = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
    
    # Check current allowance
    allowance = token.functions.allowance(wallet_addr, router_addr).call()
    
    if allowance >= amount:
        print(f"  ✓ Token already approved")
        return True
    
    print(f"  ⏳ Approving token...")
    
    try:
        nonce = w3.eth.get_transaction_count(wallet_addr)
        
        approve_tx = token.functions.approve(router_addr, 2**256 - 1).build_transaction({
            'from': wallet_addr,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        signed = w3.eth.account.sign_transaction(approve_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"  ✓ Approved! Tx: {tx_hash.hex()}")
            return True
        else:
            print(f"  ❌ Approve failed")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def get_balance(w3, token_addr, wallet_addr):
    """Get token balance"""
    token = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
    balance = token.functions.balanceOf(wallet_addr).call()
    decimals = token.functions.decimals().call()
    return balance, decimals

def swap(w3, from_token, to_token, amount_str, slippage_bps=DEFAULT_SLIPPAGE_BPS, private_key=None):
    """Execute swap on Stabilizer DEX"""
    
    # Resolve tokens
    from_addr = TOKENS.get(from_token.upper())
    to_addr = TOKENS.get(to_token.upper())
    
    if not from_addr or not to_addr:
        print(f"❌ Unknown token: {from_token} or {to_token}")
        print(f"Available: {list(TOKENS.keys())}")
        return False
    
    # Load wallet
    wallet = load_wallet(private_key)
    wallet_addr = wallet.address
    priv_key = wallet.key.hex()
    
    print(f"\n🔄 Swap: {from_token} → {to_token}")
    print(f"💰 Amount: {amount_str}")
    print(f"👛 Wallet: {wallet_addr}")
    
    # Get amount in wei (18 decimals for Stabilizer)
    amount = w3.to_wei(amount_str, 'ether')  # Stabilizer uses 18 decimals
    
    # Get balance
    balance, _ = get_balance(w3, from_addr, wallet_addr)
    balance_eth = w3.from_wei(balance, 'ether')
    
    print(f"💵 Balance: {balance_eth} {from_token}")
    
    if balance < amount:
        print(f"❌ Insufficient balance!")
        return False
    
    # Approve token
    if not approve_token(w3, from_addr, wallet_addr, priv_key, ROUTER, amount):
        return False
    
    # Calculate min receive (with slippage)
    min_receive = amount * (10000 - slippage_bps) // 10000
    
    print(f"📊 Min receive: {w3.from_wei(min_receive, 'ether')} {to_token} (slippage: {slippage_bps} bps)")
    
    # Build swap transaction
    router = w3.eth.contract(address=ROUTER, abi=STABILIZER_ROUTER_ABI)
    
    try:
        nonce = w3.eth.get_transaction_count(wallet_addr)
        
        swap_tx = router.functions.swap(from_addr, to_addr, amount, min_receive).build_transaction({
            'from': wallet_addr,
            'nonce': nonce,
            'gas': GAS_LIMIT,
            'gasPrice': w3.eth.gas_price,
            'chainId': CHAIN_ID
        })
        
        print(f"⏳ Sending transaction...")
        
        signed = w3.eth.account.sign_transaction(swap_tx, priv_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        print(f"📝 Tx: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"✅ Swap successful! Gas used: {receipt.gasUsed}")
            return True
        else:
            print(f"❌ Swap failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def quote(w3, from_token, to_token, amount_str):
    """Get quote (estimate) - for now just return amount"""
    from_addr = TOKENS.get(from_token.upper())
    to_addr = TOKENS.get(to_token.upper())
    
    if not from_addr or not to_addr:
        print(f"❌ Unknown token")
        return None
    
    amount = w3.to_wei(amount_str, 'ether')
    # Assume 1:1 for stablecoins on Stabilizer
    return amount

def main():
    if len(sys.argv) < 4:
        print("Usage: python swap.py <from_token> <to_token> <amount>")
        print("Example: python swap.py USDC USDT 5")
        sys.exit(1)
    
    from_token = sys.argv[1]
    to_token = sys.argv[2]
    amount = sys.argv[3]
    
    w3 = get_w3()
    swap(w3, from_token, to_token, amount)

if __name__ == "__main__":
    main()