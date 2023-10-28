# bungee-refuel

Refuel gas tokens between various EVM chains using [Bungee Exchange](https://www.bungee.exchange/refuel)

## Installation

Create and activate virtual environment

```
# Windows:
python -m venv .venv
.venv\Scripts\activate
```

```
# MacOS
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies

```
pip install web3 tqdm loguru
```

## Usage

Populate _keys.txt_ with your private keys, one key on each line

Specify bridging params inside _main.py_

```python
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
```

Run the file:

```python
python main.py
```

On the first execution, min/max limits will be fetched from [https://refuel.socket.tech/chains](https://docs.socket.tech/socket-api/v2/guides/refuel-integration) and cached for subsequent usage.
To refresh the data, simply delete _refuel.json_ file inside the project folder.

Logs will be availible inside _debug.log_
