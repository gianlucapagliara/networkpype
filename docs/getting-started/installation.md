# Installation

## Requirements

- Python 3.13 or higher

## Install from PyPI

```bash
# Using pip
pip install networkpype

# Using uv
uv add networkpype

# Using poetry
poetry add networkpype
```

## Dependencies

NetworkPype has two runtime dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| [aiohttp](https://docs.aiohttp.org/) | >= 3.10.0 | Async HTTP and WebSocket client |
| [numpy](https://numpy.org/) | >= 2.2.2 | Time offset statistics in `TimeSynchronizer` |

## Verify Installation

```python
import networkpype
from networkpype.factory import ConnectionManagersFactory, ConnectionsFactory
from networkpype.throttler.throttler import AsyncThrottler
from networkpype.throttler.rate_limit import RateLimit

print("networkpype installed successfully")
```
