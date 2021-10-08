# Flask-LDP

Work in progres ...

[![PyPI version](https://badge.fury.io/py/Flask-LDP.svg)](https://badge.fury.io/py/Flask-LDP)

Fork of [https://github.com/gridscale/flask-graylog2](https://github.com/gridscale/flask-graylog2) to support OVH Logs Data Platform.

Which is himself a fork of [github.com/underdogio/flask-graylog](https://github.com/underdogio/flask-graylog) with additional patches and features.

This is a Flask extension that allows you to configure a OVH Logs Data Platform (LDP) logging handler as well as some middleware to log every request/response pair to Graylog.

See also:

- [Flask docs](https://flask.palletsprojects.com/en/1.1.x/logging/)
- [Graylog docs](https://docs.graylog.org/en/latest/index.html)
- [graypy docs](https://graypy.readthedocs.io/en/stable/?badge=stable#)
- [OVH docs](https://docs.ovh.com/fr/logs-data-platform/)

## Installation

You can install it with [`pip`](https://pypi.org/):

    $ pip install Flask-LDP

## Usage

You only need to import and initialize your app

```python
# Import dependencies
from flask import Flask
from flask_ldp import LDP

# Configure app and LDP logger
app = Flask(__name__)
ldp = LDP(app)

# Log to ldp
ldp.info("Message", extra={"data": "metadata",})

# Use LDP log handler in another logger
import logging

logger = logging.getLogger(__name__)
logger.addHandler(ldp.handler)
logger.info("Message")
```

## Configuration options

The following options can be use to configure the ldp logger.

```python
from flask import Flask
from flask_ldp import LDP

app = Flask(__name__)

# Use configuration from `app`
app.config["LDP_HOSTNAME"] = "gra3.logs.ovh.com"
app.config["LDP_TOKEN"] = "xxxxxx"
ldp = LDP(app)

# Provide configuration
config = {"LDP_HOSTNAME": "gra3.logs.ovh.com", "LDP_TOKEN": "xxxxx"}
ldp = LDP(app, config=config)
```

- `LDP_HOSTNAME` - the host to send messages to [default: 'gra3.logs.ovh.com']
- `LDP_TOKEN` - the token [default: None]
```
