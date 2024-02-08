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

Specify bridging params inside _settings.py_

Run _main.py_

```python
python main.py
```

Refuel's min/max limits are fetched from [https://refuel.socket.tech/chains](https://docs.socket.tech/socket-api/v2/guides/refuel-integration) and cached for 1 hour to avoid 429 Too Many Requests error. Adjust cache max age in _settings.py_ or simply delete _refuel.json_ file inside the project folder to refresh the data.

Transaction logs are availible inside _debug.log_
