# unimonapi

Universal API for different monitoring systems: use built-in system types or extend with your own.

Currently supported API is [Zabbix](https://zabbix.com). But you can extend the package with any monitoring system you want.

Just imagine: universal API for every system!

## Getting Started

### Installing

To install the package simply run:

```bash
pip install unimonapi
```

### Using

The unimonapi CLI is available just after installation:

```bash
zabbix_cli.py --help
```

Or of course you can use the package for coding:

```python
from unimonapi import ZabbixAPI
api = ZabbixAPI('http://zabbix-web', 'Admin', 'zabbix')
for problem in api.get_problems():
    print problem
```

## Extending

Extending the package is simple:

```python
import requests
from unimonapi import MonitoringAPI
from unimonapi import Event

class MyMonAPI(MonitoringAPI):

    def __init__(self, url):
        self.url = url

    def get_problems(self, severities=None, groups=None):
        problems = []
        for p in requests.get(self.url).json():
            if severities is None or p['severity'] in severities:
                if groups is None or p['group'] in groups:
                    event = Event(Event.PROBLEM, True, p['severity'], p['host'], p['text'], p['id'])
                    problems.append(event)
        return problems
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
