# set the source and destination chains
# ethereum | optimism | bsc | gnosis | polygon | zksync
# zkevm | base | arbitrum | avalanche | aurora
FROM_CHAIN = "ethereum"
TO_CHAIN = "zksync"

# choose refuel mode
# 'min' for minimum alowed amount
# 'max' for maximum alowed amount 
# 'exact' for an exact token amount
# max percentage delta for min/max mode
MODE = 'min'
MAX_DELTA = 3 # 3%

# specify the amount range in 'exact' mode in native token: ETH / BNB / AVAX / MATIC etc
AMOUNT_FROM = 0.0013
AMOUNT_TO = 0.0018

# set the sleep duration between wallets in seconds
MIN_SLEEP = 60
MAX_SLEEP = 120
