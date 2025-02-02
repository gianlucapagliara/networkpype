# Network Pypeline

[![PyPI version](https://badge.fury.io/py/networkpype.svg)](https://badge.fury.io/py/networkpype)
[![Python](https://img.shields.io/pypi/pyversions/networkpype.svg?style=plastic)](https://badge.fury.io/py/networkpype)
[![Documentation Status](https://readthedocs.org/projects/networkpype/badge/?version=latest)](https://networkpype.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A powerful Python library for building efficient network communication pipelines, supporting both REST and WebSocket protocols with built-in rate limiting and time synchronization.

## Features

- 🔄 **Dual Protocol Support**: Seamlessly handle both REST and WebSocket communications
- 🚦 **Rate Limiting**: Built-in throttling mechanism to respect API rate limits
- ⏰ **Time Synchronization**: Automatic time synchronization for accurate API interactions
- 🏭 **Factory Pattern**: Easy-to-use factory for creating and managing connections
- 🔌 **Modular Design**: Extensible processor architecture for custom request/response handling
- 🛡️ **Type Safety**: Full type hinting support for better development experience

## Installation

Install using pip:

```bash
pip install networkpype
```

Or with Poetry:

```bash
poetry add networkpype
```

## Quick Start

### REST Example

```python
from networkpype.factory import ConnectionFactory
from networkpype.rest.method import Method

# Create a REST connection
factory = ConnectionFactory()
connection = factory.create_rest_connection(
    base_url="https://api.example.com",
    rate_limit=100  # requests per minute
)

# Make a request
response = connection.request(
    method=Method.GET,
    endpoint="/users",
    params={"page": 1}
)
```

### WebSocket Example

```python
from networkpype.factory import ConnectionFactory

# Create a WebSocket connection
factory = ConnectionFactory()
connection = factory.create_websocket_connection(
    url="wss://ws.example.com"
)

# Subscribe to updates
connection.subscribe(
    channel="market.btcusdt.trade",
    callback=lambda msg: print(f"Received: {msg}")
)
```

## Documentation

For detailed documentation, please visit [networkpype.readthedocs.io](https://networkpype.readthedocs.io/).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.