from web3 import Web3
from web3.middleware import geth_poa_middleware
from loguru import logger
import random
import csv

from utils import load_shuffled_keys, get_abi, fetch_refuel_data, sleep
from data import chain_data, bungee_contract_address, bungee_destinationChainId


# Config | ethereum | optimism | bsc | gnosis | polygon |
# zksync | zkevm | base | arbitrum  | avalanche | aurora
FROM_CHAIN = "ethereum"
TO_CHAIN = "zksync"

# if True will use the MIN amount allowed for selected route
# boosted by a small percentage up to MAX_BOOST value
USE_MIN = True
MAX_BOOST = 3  # 3%

# Otherwise, specify the amount range in native token: ETH/BNB/AVAX/MATIC etc
AMOUNT_FROM = 0.0013
AMOUNT_TO = 0.0018

# Sleep between wallets in seconds
MIN_SLEEP = 30
MAX_SLEEP = 60


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

failed_wallets = []


def get_chain_limits():
    refuel_api_data = fetch_refuel_data(update=False, json_cache="refuel.json")

    for chain in refuel_api_data["result"]:
        if origin_id == chain["chainId"]:
            for limit in chain["limits"]:
                if dest_id == limit["chainId"]:
                    is_enabled = bool(limit["isEnabled"])
                    min_amount = int(limit["minAmount"])
                    max_amount = int(limit["maxAmount"])

                    if not is_enabled:
                        raise ValueError("Refuel isn't supported for this route")

                    print(
                        f"{origin} => {dest} is allowed | min {web3.from_wei(min_amount, 'ether')} {token_symbol} | max {web3.from_wei(max_amount, 'ether')} {token_symbol}\n"
                    )

                    return min_amount, max_amount


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
            # set gas price to 1 gwei
            tx["gasPrice"] = 1000000000

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
        logger.error(f"Wallet {wallet_address} | {error}\n")
        failed_wallets.append((wallet_address, private_key, error))
        return False


def main():
    try:
        keys_list = load_shuffled_keys()
        min_amount, max_amount = get_chain_limits()

        try:
            print("Press 'Enter' to continue or 'Ctrl + C' to exit")
            input()
        except KeyboardInterrupt:
            print("\nYou pressed Ctrl + C. Exiting...")
            return

        while keys_list:
            key = keys_list.pop(0)
            logger.info(f"Wallet: {web3.eth.account.from_key(key).address}")

            if USE_MIN:
                percentage_increase = random.randint(1, MAX_BOOST)
                amount = int(min_amount * (1 + percentage_increase / 100))
            else:
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

    # Save the failed wallets to a CSV file
    if failed_wallets:
        with open("failed_wallets.csv", "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Address", "Private Key", "Error"])
            writer.writerows(failed_wallets)


if __name__ == "__main__":
    main()
