from web3 import Web3
from web3.middleware import geth_poa_middleware
from loguru import logger
import random

from utils import load_shuffled_keys, get_abi, fetch_refuel_data, sleep
from data import chain_data, bungee_contract_address, bungee_destinationChainId


# Config | ethereum | optimism | bsc | gnosis | polygon | 
# zksync | zkevm | base | arbitrum  | avalanche | aurora  
FROM_CHAIN = "ethereum"
TO_CHAIN = "zksync"

# MIN & MAX amount in native token (ETH/BNB/AVAX/MATIC etc)
AMOUNT_FROM = 0.0012  
AMOUNT_TO = 0.0018  

# Sleep between wallets in seconds
MIN_SLEEP = 20
MAX_SLEEP = 30

logger.add(
    "debug.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",
)

# Connect to a node and inject the POA compatibility middleware for Avalanche, Polygon, BSC etc
web3 = Web3(Web3.HTTPProvider(chain_data[FROM_CHAIN]["chain_rpc"]))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Initialize the refuel contract and set global variables
bungee_contract = web3.eth.contract(address=web3.to_checksum_address(bungee_contract_address[FROM_CHAIN]), abi=get_abi())
destinationChainId = bungee_destinationChainId[TO_CHAIN]

explorer_base_url = chain_data[FROM_CHAIN]["block_explorer"]
token_symbol = chain_data[FROM_CHAIN]["native_asset"]
origin = chain_data[FROM_CHAIN]["chain_name"]
dest = chain_data[TO_CHAIN]["chain_name"]
origin_id = chain_data[FROM_CHAIN]["chain_id"]
dest_id = chain_data[TO_CHAIN]["chain_id"]


def get_chain_limits():
    refuel_api_data = fetch_refuel_data(update=False, json_cache="refuel.json")

    for chain in refuel_api_data["result"]:
        if origin_id == chain["chainId"]:
            for limit in chain["limits"]:
                if dest_id == limit["chainId"]:
                    return bool(limit["isEnabled"]), int(limit["minAmount"]), int(limit["maxAmount"])


def bungee_refuel(amount, private_key):
    wallet_address = web3.eth.account.from_key(private_key).address
    nonce = web3.eth.get_transaction_count(wallet_address)

    try:
        # Build the transaction
        tx = bungee_contract.functions.depositNativeToken(destinationChainId, wallet_address).build_transaction(
            {"from": wallet_address, "value": amount, "nonce": nonce}
        )

        # Fallback for Binance Smart Chain
        if FROM_CHAIN == "bsc":
            del tx["maxFeePerGas"]
            del tx["maxPriorityFeePerGas"]
            tx["gasPrice"] = web3.eth.gas_price

        # Sign and send the transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Tx submitted: {explorer_base_url}/tx/{tx_hash.hex()}")

        # Wait for the transaction to be mined
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=400)

        if tx_receipt.status:
            logger.success(f"Tx confirmed: {origin}  => {dest} | {web3.from_wei(amount, 'ether')} {token_symbol}\n")
            return True
        else:
            raise ValueError("Tx failed")

    except Exception as error:
        logger.error(f"wallet {wallet_address} | {error}\n")
        return False


def main():
    try:
        keys_list = load_shuffled_keys()
        print(f"\nWallet(s) loaded: {len(keys_list)}")
        is_refuel_enabled, min_amount, max_amount = get_chain_limits()

        if not is_refuel_enabled:
            raise ValueError("Refuel isn't supported for this route")

        logger.info(
            f"{origin}  => {dest} is allowed | min {web3.from_wei(min_amount, 'ether')} {token_symbol} | max {web3.from_wei(max_amount, 'ether')} {token_symbol}\n"
        )

        while keys_list:
            key = keys_list.pop(0)
            amount = random.randint(web3.to_wei(AMOUNT_FROM, "ether"), web3.to_wei(AMOUNT_TO, "ether"))

            if amount < min_amount or amount > max_amount:
                raise ValueError(
                    f"Selected amount is outside of allowed range: {web3.from_wei(min_amount, 'ether')} to {web3.from_wei(max_amount, 'ether')} {token_symbol}\n"
                )

            success = bungee_refuel(amount, key)

            if keys_list and success:
                sleep(MIN_SLEEP, MAX_SLEEP)

    except Exception as error:
        logger.error(f"An error occurred: {str(error)}")


if __name__ == "__main__":
    main()
