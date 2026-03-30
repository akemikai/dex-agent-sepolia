"""
DEX Agent — Sepolia + Stabilizer (Python)
Multi-wallet auto-swap with delay and loop
"""

import os
import sys
import time
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

RPC_URL = env.get('RPC_URL', 'https://sepolia.infura.io/v3/84842078b09946638c03157f83405213')
CHAIN_ID = 11155111
MAX_TX = int(env.get('MAX_TX', '1'))
DELAY = int(env.get('DELAY', '30'))

TOKENS = {
    "USDC": Web3.to_checksum_address("0x77ef087024F87976aAdA0Aa7F73BB8EAe6E9dda1"),
    "USDT": Web3.to_checksum_address("0xee0418Bd560613fbcF924C36235AB1ec301D4933"),
    "USDZ": Web3.to_checksum_address("0x55Cc481D28Db3f1ffc9347745AA6fbB940505BdD"),
}

ROUTER = Web3.to_checksum_address("0xfa6419a3d3503a016df3a59f690734862ca2a78d")

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

def swap_for_wallet(w3, private_key, from_token, to_token, amount_str, max_tx, delay):
    """Execute swaps for one wallet"""
    
    account = w3.eth.account.from_key(private_key)
    wallet_addr = Web3.to_checksum_address(account.address)
    
    from_addr = TOKENS.get(from_token)
    to_addr = TOKENS.get(to_token)
    
    if not from_addr or not to_addr:
        print(f"❌ Unknown token")
        return 0, 0, 0
    
    amount_wei = w3.to_wei(amount_str, 'ether')
    
    token = w3.eth.contract(address=from_addr, abi=ERC20_ABI)
    balance = token.functions.balanceOf(wallet_addr).call()
    
    print(f"\n👛 Wallet: {wallet_addr}")
    print(f"   💰 Balance: {w3.from_wei(balance, 'ether')} {from_token}")
    
    if balance < amount_wei:
        print(f"   ❌ Insufficient balance!")
        return 0, 0, 0
    
    # Approve
    print(f"   ⏳ Approving...")
    try:
        nonce = w3.eth.get_transaction_count(wallet_addr)
        approve_tx = token.functions.approve(ROUTER, 2**256 - 1).build_transaction({
            'from': wallet_addr, 'nonce': nonce, 'gas': 100000,
            'gasPrice': 119571, 'chainId': CHAIN_ID
        })
        signed = w3.eth.account.sign_transaction(approve_tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"   ✅ Approved!")
    except Exception as e:
        print(f"   ⚠️ Approve error: {e}")
    
    # Start loop
    router = w3.eth.contract(address=ROUTER, abi=STABILIZER_ROUTER_ABI)
    success_count = 0
    fail_count = 0
    total_gas = 0
    
    for i in range(1, max_tx + 1):
        print(f"   📝 Swap #{i}/{max_tx}...")
        
        balance = token.functions.balanceOf(wallet_addr).call()
        if balance < amount_wei:
            print(f"   ❌ Insufficient balance!")
            break
        
        try:
            nonce = w3.eth.get_transaction_count(wallet_addr)
            swap_tx = router.functions.swap(from_addr, to_addr, amount_wei, 0).build_transaction({
                'from': wallet_addr, 'nonce': nonce, 'gas': 815109,
                'gasPrice': 119571, 'chainId': CHAIN_ID
            })
            
            signed = w3.eth.account.sign_transaction(swap_tx, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                success_count += 1
                total_gas += receipt.gasUsed
                print(f"   ✅ Success! https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
            else:
                fail_count += 1
                print(f"   ❌ Failed!")
                
        except Exception as e:
            fail_count += 1
            print(f"   ❌ Error: {str(e)[:40]}")
        
        if i < max_tx:
            print(f"   ⏳ Waiting {delay}s...")
            time.sleep(delay)
    
    return success_count, fail_count, total_gas

def main():
    # Parse args
    wallets = []
    from_token = "USDC"
    to_token = "USDT"
    amount_str = "60"
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ["-w", "--wallet"]:
            if i + 1 < len(sys.argv):
                wallets.append(sys.argv[i + 1])
                i += 2
            else:
                print(f"❌ Missing wallet private key after {arg}")
                return
        elif arg in ["-f", "--from"]:
            if i + 1 < len(sys.argv):
                from_token = sys.argv[i + 1].upper()
                i += 2
            else:
                print(f"❌ Missing token after {arg}")
                return
        elif arg in ["-t", "--to"]:
            if i + 1 < len(sys.argv):
                to_token = sys.argv[i + 1].upper()
                i += 2
            else:
                print(f"❌ Missing token after {arg}")
                return
        elif arg in ["-a", "--amount"]:
            if i + 1 < len(sys.argv):
                amount_str = sys.argv[i + 1]
                i += 2
            else:
                print(f"❌ Missing amount after {arg}")
                return
        else:
            i += 1
    
    # Check wallets from env PRIVATE_KEY, PRIVATE_KEY_2, etc
    if not wallets:
        if 'PRIVATE_KEY' in env:
            wallets.append(env['PRIVATE_KEY'])
        for key in env:
            if key.startswith('PRIVATE_KEY_') and env[key]:
                wallets.append(env[key])
    
    if not wallets:
        print("❌ No wallet found!")
        print("\nUsage: python3 swap.py [options]")
        print("Options:")
        print("  -w, --wallet <pk>  Add wallet private key (can use multiple)")
        print("  -f, --from <token> From token (USDC, USDT, USDZ)")
        print("  -t, --to <token>   To token")
        print("  -a, --amount <amt> Amount per swap")
        print("\nOr set in .env:")
        print("  PRIVATE_KEY=0x...")
        print("  PRIVATE_KEY_2=0x...")
        print("  MAX_TX=10")
        print("  DELAY=30")
        return
    
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    print(f"✅ Connected to Sepolia (block: {w3.eth.block_number})")
    
    print(f"\n🚀 Auto-Swap Starting")
    print(f"   From: {from_token} → {to_token}")
    print(f"   Amount: {amount_str}")
    print(f"   Max TX: {MAX_TX}")
    print(f"   Delay: {DELAY}s")
    print(f"   Wallets: {len(wallets)}")
    print("="*50)
    
    total_success = 0
    total_fail = 0
    total_gas = 0
    
    # Run for each wallet
    for idx, wallet_pk in enumerate(wallets, 1):
        print(f"\n{'='*50}")
        print(f"🏦 WALLET {idx}/{len(wallets)}")
        
        success, fail, gas = swap_for_wallet(w3, wallet_pk, from_token, to_token, amount_str, MAX_TX, DELAY)
        
        total_success += success
        total_fail += fail
        total_gas += gas
        
        print(f"   📊 Wallet {idx} result: ✅{success} ❌{fail}")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"📊 FINAL SUMMARY")
    print(f"   ✅ Total Success: {total_success}")
    print(f"   ❌ Total Failed:  {total_fail}")
    print(f"   ⛽ Total Gas:     {total_gas}")
    print(f"   🛑 Stopped")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()