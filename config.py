from loguru import logger

from sys import stderr
import json

from data.data import chain_data, bungee_contract_address, bungee_destinationChainId
from settings import *


logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>")
logger.add("debug.log", format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>", level="DEBUG")

explorer_base_url = chain_data[FROM_CHAIN]["block_explorer"]
token_symbol = chain_data[FROM_CHAIN]["native_asset"]
origin = chain_data[FROM_CHAIN]["chain_name"]
dest = chain_data[TO_CHAIN]["chain_name"]
origin_id = chain_data[FROM_CHAIN]["chain_id"]
dest_id = chain_data[TO_CHAIN]["chain_id"]
destinationChainId = bungee_destinationChainId[TO_CHAIN]
contract = bungee_contract_address[FROM_CHAIN]
rpc = chain_data[FROM_CHAIN]["chain_rpc"]

with open(f"data/abi.json", "r") as file:
    abi = json.load(file)
    
