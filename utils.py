import json
from tqdm import tqdm
import requests
import random
import time


def load_shuffled_keys():
    with open("keys.txt", "r") as f:
        keys = [row.strip() for row in f]

        if not keys:
            raise ValueError("keys.txt is empty or not properly formatted")

        random.shuffle(keys)
        print(f"\n>>> Wallet(s) loaded: {len(keys)}")
        return keys


def get_abi(path="abi.json"):
    with open(path, "r") as f:
        return json.load(f)


def fetch_refuel_data(*, update=False, json_cache, url="https://refuel.socket.tech/chains"):
    if update:
        json_data = None
    else:
        try:
            with open(json_cache, "r") as f:
                json_data = json.load(f)
                print("Using refuel data from local json cache \n")
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
    for i in tqdm(range(x), desc="sleeping for", bar_format="{desc}: {n_fmt}/{total_fmt} seconds"):
        time.sleep(1)
    print()
