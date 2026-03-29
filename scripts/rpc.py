"""
RPC Configuration — Sepolia Testnet
"""

import os
from web3 import Web3

from config import RPC_URL, BACKUP_RPC

_w3 = None

def get_w3():
    """Get Web3 instance"""
    global _w3
    
    if _w3 is None:
        _w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not _w3.is_connected():
            print(f"⚠️  Primary RPC failed, trying backup...")
            _w3 = Web3(Web3.HTTPProvider(BACKUP_RPC))
        
        if _w3.is_connected():
            print(f"✅ Connected to Sepolia (block: {_w3.eth.block_number})")
        else:
            raise Exception("❌ Failed to connect to Sepolia")
    
    return _w3

def get_chain_id():
    return 11155111  # Sepolia