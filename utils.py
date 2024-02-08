import requests
from tqdm import tqdm

import json
import random
import time
import os
from decimal import Decimal
from datetime import datetime, timedelta

from settings import CACHE_MAX_AGE


def load_shuffled_keys():
    with open("files/keys.txt", "r") as f:
        keys = [row.strip() for row in f]

        if not keys:
            raise ValueError("keys.txt is empty or not properly formatted")

        random.shuffle(keys)
        print(f"\n>>> Wallet(s) loaded: {len(keys)}")
        return keys


def fetch_refuel_data(*, update=False, json_cache, url="https://refuel.socket.tech/chains"):
    if update:
        json_data = None
    else:
        try:
            # Check the modification time of the file
            file_stat = os.stat(json_cache)
            last_modified_time = datetime.fromtimestamp(file_stat.st_mtime)
            current_time = datetime.now()
            time_difference = current_time - last_modified_time

            if time_difference < timedelta(hours=CACHE_MAX_AGE):
                with open(json_cache, "r") as f:
                    json_data = json.load(f)
                    print("Using refuel data from local json cache \n")
            else:
                print(f"Local cache is older than {CACHE_MAX_AGE} hours. Fetching refuel data from remote api \n")
                json_data = None

        except FileNotFoundError:
            print(f"No local cache found...")
            json_data = None

    if not json_data:
        print("Fetching refuel data from remote api \n")
        json_data = requests.get(url).json()
        with open(json_cache, "w") as f:
            json.dump(json_data, f, indent=4)

    return json_data


def sleep(MIN_SLEEP, MAX_SLEEP):
    x = random.randint(MIN_SLEEP, MAX_SLEEP)
    for _ in tqdm(range(x), desc="sleeping for", bar_format="{desc}: {n_fmt}/{total_fmt} seconds"):
        time.sleep(1)
    print()
    
    
def get_token_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        response = requests.get(url)
        data = response.json()
        
        return Decimal(data["price"])
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching token price: {e}")
        return None
    
    
def calc_usd_amount(token_price, amount):
    usd_amount = token_price * Decimal(amount / 10**18)
    return round(usd_amount, 2)


def print_route_summary(origin, dest, min_amount, max_amount, token_symbol):
    token_price = get_token_price(token_symbol)
    
    if token_price:
        min_usd = calc_usd_amount(token_price, min_amount)
        max_usd = calc_usd_amount(token_price, max_amount)
        
        print(
            f"{origin} => {dest} | "
            f"min {min_amount / 1e18:.10f} {token_symbol} (${round(min_usd, 2)}) | "
            f"max {max_amount / 1e18:.10f} {token_symbol} (${round(max_usd, 2)})",
            end='\n'
        )
        
        return token_price
    else:
       print(
            f"{origin} => {dest} | "
            f"min {min_amount / 1e18} {token_symbol} | "
            f"max {max_amount / 1e18} {token_symbol}",
            end='\n'
        ) 
