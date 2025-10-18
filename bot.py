import json
import random
import time
from datetime import datetime

# --- Lightweight/faster helpers ---
def _fast_hex(n_bytes=8):
    """Generate short hex string quickly (n_bytes default 8 -> 16 hex chars)."""
    return "0x" + format(random.getrandbits(n_bytes * 8), "x").rjust(n_bytes * 2, "0")

def _now_ts():
    """Single fast timestamp call."""
    return int(time.time())

def _to_wei(val, unit):
    if unit == "ether":
        return int(float(val) * 10**18)
    if unit == "gwei":
        return int(float(val) * 10**9)
    return int(val)

# --- Dummy web3/account simulation classes (lightweight) ---
class DummyEth:
    def contract(self, address=None, abi=None):
        return DummyContract(address, abi)
    def get_block(self, arg):
        return {"timestamp": _now_ts()}
    def get_transaction_count(self, address):
        # small deterministic-ish nonce for demo
        return random.randint(0, 20)
    def send_raw_transaction(self, raw):
        # return bytes-like txhash (short)
        hx = _fast_hex(8)[2:]  # 8 bytes -> 16 hex chars
        return bytes.fromhex(hx)

class DummyWeb3:
    def __init__(self):
        self.eth = DummyEth()
    def to_wei(self, val, unit):
        return _to_wei(val, unit)
    def to_hex(self, b):
        return "0x" + b.hex() if isinstance(b, (bytes, bytearray)) else str(b)
    def to_checksum_address(self, a):
        return a

class DummyAccount:
    def __init__(self, private_key):
        # Generate a short dummy address (not real)
        self.address = "0x" + format(random.getrandbits(160), "x").rjust(40, "0")
    def sign_transaction(self, tx):
        class Signed:
            rawTransaction = b"dummy_tx"
        return Signed()

class DummyFunction:
    def __init__(self, name, return_val=None, build_template=None):
        self.name = name
        self.return_val = return_val
        self.build_template = build_template
    def call(self):
        if self.name == "balanceOf":
            # smaller random balance to avoid huge ints, still simulated
            return random.randint(1, 10**18)
        if self.name == "decimals":
            return 18
        if self.name == "symbol":
            return "TOK"
        return self.return_val or 0
    def build_transaction(self, txdict):
        # Lightweight tx dict (keeps same keys used in original script)
        tx = {
            "from": txdict.get("from"),
            "to": txdict.get("to", "0xDummy"),
            "value": txdict.get("value", 0),
            "gas": txdict.get("gas"),
            "gasPrice": txdict.get("gasPrice"),
            "nonce": txdict.get("nonce"),
            "data": "<dummy_data>"
        }
        if self.build_template:
            tx.update(self.build_template)
        return tx

class DummyContract:
    def __init__(self, address=None, abi=None):
        self.address = address or "0xDummyContract"
        self.abi = abi or []
        # functions container similar to web3 contract.functions
        self.functions = self
    def balanceOf(self, addr):
        return DummyFunction("balanceOf")
    def decimals(self):
        return DummyFunction("decimals")
    def symbol(self):
        return DummyFunction("symbol")
    def approve(self, spender, value):
        return DummyFunction("approve", build_template={"approved_to": spender, "approved_value": value})
    def swapExactETHForTokens(self, *args, **kwargs):
        return DummyFunction("swapExactETHForTokens", build_template={"swap": "eth->tokens"})
    def swapExactTokensForETH(self, *args, **kwargs):
        return DummyFunction("swapExactTokensForETH", build_template={"swap": "tokens->eth"})

# ---------- Dummy Config (kept similar names) ----------
ANKR_RPC = "https://rpc.ankr.com/multichain/f943d482902e1f866767c57053e9e5db3575dd95e27a5e79c68463005b0a0259"
PRIVATE_KEY = "YOUR_PRIVATE_KEY_HERE"  # still placeholder in dummy
ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"

# Initialize dummy web3 & account (fast)
web3 = DummyWeb3()
account = DummyAccount(PRIVATE_KEY)
ADDRESS = account.address

# ---------- Router ABI (unchanged) ----------
UNISWAP_ROUTER_ABI = json.loads("""
[
  {
    "name": "swapExactETHForTokens",
    "type": "function",
    "inputs": [
      {"name": "amountOutMin", "type": "uint256"},
      {"name": "path", "type": "address[]"},
      {"name": "to", "type": "address"},
      {"name": "deadline", "type": "uint256"}
    ],
    "outputs": [{"name": "amounts", "type": "uint256[]"}],
    "stateMutability": "payable"
  },
  {
    "name": "swapExactTokensForETH",
    "type": "function",
    "inputs": [
      {"name": "amountIn", "type": "uint256"},
      {"name": "amountOutMin", "type": "uint256"},
      {"name": "path", "type": "address[]"},
      {"name": "to", "type": "address"},
      {"name": "deadline", "type": "uint256"}
    ],
    "outputs": [{"name": "amounts", "type": "uint256[]"}],
    "stateMutability": "nonpayable"
  }
]
""")

# Router (dummy contract instance)
router = web3.eth.contract(address=web3.to_checksum_address(ROUTER_ADDRESS), abi=UNISWAP_ROUTER_ABI)

# ---------- Core functions (same signatures & flow) ----------
def check_token_balance(token_address):
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        }
    ]
    token = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=erc20_abi)
    # single fast timestamp (not necessary here but consistent)
    # Simulated calls (fast)
    raw_balance = token.functions.balanceOf(ADDRESS).call()
    decimals = token.functions.decimals().call()
    symbol = token.functions.symbol().call()
    balance = raw_balance / (10 ** decimals)
    # return formatted like original
    return f"{balance:.4f} {symbol}"

def swap_buy(token_address, eth_amount):
    token_address = web3.to_checksum_address(token_address)
    path = [web3.to_checksum_address(WETH_ADDRESS), token_address]
    now = web3.eth.get_block("latest")["timestamp"]
    deadline = now + 1200

    tx = router.functions.swapExactETHForTokens(
        0,  # Accept any amount out
        path,
        ADDRESS,
        deadline
    ).build_transaction({
        "from": ADDRESS,
        "value": web3.to_wei(eth_amount, "ether"),
        "gas": 250000,
        "gasPrice": web3.to_wei("5", "gwei"),
        "nonce": web3.eth.get_transaction_count(ADDRESS)
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return f"Buy Tx Sent: {web3.to_hex(tx_hash)}"

def swap_sell(token_address, percentage=100):
    token_address = web3.to_checksum_address(token_address)
    erc20_abi = [
        {
            "constant": False,
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        }
    ]
    token = web3.eth.contract(address=token_address, abi=erc20_abi)
    # Simulated calls
    balance = token.functions.balanceOf(ADDRESS).call()
    decimals = token.functions.decimals().call()
    sell_amount = int(balance * percentage / 100)

    # Approve (simulated)
    approve_tx = token.functions.approve(web3.to_checksum_address(ROUTER_ADDRESS), sell_amount).build_transaction({
        "from": ADDRESS,
        "gas": 80000,
        "gasPrice": web3.to_wei("5", "gwei"),
        "nonce": web3.eth.get_transaction_count(ADDRESS)
    })
    signed_approve = account.sign_transaction(approve_tx)
    web3.eth.send_raw_transaction(signed_approve.rawTransaction)

    # Sell
    path = [token_address, web3.to_checksum_address(WETH_ADDRESS)]
    now = web3.eth.get_block("latest")["timestamp"]
    deadline = now + 1200

    sell_tx = router.functions.swapExactTokensForETH(
        sell_amount,
        0,
        path,
        ADDRESS,
        deadline
    ).build_transaction({
        "from": ADDRESS,
        "gas": 250000,
        "gasPrice": web3.to_wei("5", "gwei"),
        "nonce": web3.eth.get_transaction_count(ADDRESS)
    })
    signed_sell = account.sign_transaction(sell_tx)
    tx_hash = web3.eth.send_raw_transaction(signed_sell.rawTransaction)
    return f"Sell Tx Sent: {web3.to_hex(tx_hash)}"

# ---------- Demo block so running the script shows output immediately ----------
if __name__ == "__main__":
    sample_token = "0x000000000000000000000000000000000000dead"
    print("Checking token balance...")
    balance = check_token_balance(sample_token)
    print("Balance:", balance)

    print("\nSimulating buy...")
    buy_tx = swap_buy(sample_token, 0.01)
    print(buy_tx)

    print("\nSimulating sell...")
    sell_tx = swap_sell(sample_token, 50)
    print(sell_tx)

    print("\nDemo run complete!")
