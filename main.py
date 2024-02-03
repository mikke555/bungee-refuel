from web3 import Web3
from web3.middleware import geth_poa_middleware

import random
import csv

from utils import load_shuffled_keys, fetch_refuel_data, sleep
from config import logger, explorer_base_url, token_symbol, origin, dest, origin_id, dest_id, destinationChainId, rpc, contract, abi
from settings import *


# Connect to a node provider
web3 = Web3(Web3.HTTPProvider(rpc))
# inject the POA compatibility middleware for Avalanche, Polygon, BSC etc
web3.middleware_onion.inject(geth_poa_middleware, layer=0)
# Initialize bungee refuel contract
bungee_contract = web3.eth.contract(address=web3.to_checksum_address(contract), abi=abi)

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
        tx = bungee_contract.functions.depositNativeToken(destinationChainId, wallet_address).build_transaction({ 
            "from": wallet_address, 
            "value": amount, 
            "nonce": nonce, 
        })
       
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
        keys_len = len(keys_list)
        min_amount, max_amount = get_chain_limits()

        try:
            print("Press Enter to continue or Ctrl + C to exit")
            input()
        except KeyboardInterrupt:
            return

        while keys_list:
            key = keys_list.pop(0)
            logger.info(f"Wallet [{keys_len - len(keys_list)}/{keys_len}]: {web3.eth.account.from_key(key).address}")

            random_delta = random.randint(1, MAX_DELTA)
            
            if MODE == 'min':
                amount = int(min_amount * (1 + random_delta / 100))
            if MODE == 'max':
                amount = max_amount - int(max_amount * (random_delta / 100))
            if MODE == 'exact':
                amount = random.randint(web3.to_wei(AMOUNT_FROM, "ether"), web3.to_wei(AMOUNT_TO, "ether"))

            if amount < min_amount or amount > max_amount:
                raise ValueError(
                    f"Selected value is outside min/max range: {web3.from_wei(min_amount, 'ether')} - {web3.from_wei(max_amount, 'ether')} {token_symbol}\n"
                )

            success = bungee_refuel(amount, key)

            if keys_list and success:
                sleep(MIN_SLEEP, MAX_SLEEP)

    except Exception as error:
        logger.error(f"{str(error)}")

    # Save the failed wallets to a CSV file
    if failed_wallets:
        with open("failed_wallets.csv", "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Address", "Private Key", "Error"])
            writer.writerows(failed_wallets)


if __name__ == "__main__":
    main()
