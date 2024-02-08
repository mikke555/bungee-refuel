# set the source and destination chains
# ethereum | optimism | bsc | gnosis | polygon | zksync
# zkevm | base | arbitrum | avalanche | aurora
FROM_CHAIN = "ethereum"
TO_CHAIN = "zksync"

# choose refuel mode
# 'min' for minimum allowed amount
# 'max' for maximum allowed amount 
# 'exact' for an exact token amount
MODE = 'min'
MAX_BOOST = 3 # 3%

# amount range in 'exact' mode in native token: ETH / BNB / AVAX / MATIC etc
AMOUNT_FROM = 0.0013
AMOUNT_TO = 0.0018

# sleep duration between wallets in seconds
MIN_SLEEP = 60
MAX_SLEEP = 120

# max age for json cache in hours
CACHE_MAX_AGE = 1
