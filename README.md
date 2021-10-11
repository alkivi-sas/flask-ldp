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

## ⚙️ Configuration options

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

## 🪵 Additionnal data to log

You can send a few extra data, as provided with by the default schema.
```python
class DefaultLoggingkSchema(LDPSchema):
    user = fields.Raw()
    data = fields.Raw()
    flask = fields.Raw()
    request = fields.Raw()
    response = fields.Raw()
```

Example

```python

something_json_dumpable = dict(toto='titi')
extra_data = dict(
    data=something_json_dumpable,
    user=something_json_dumpable,
)
ldp.info("Message", extra=extra_data)
```

You can also dump flask information and request data 
```python
ldp.info("Message", add_flask=True, add_request=True)

# Under the hood
if 'add_flask' in kwargs:
    extra['flask'] = {"endpoint": str(request.endpoint).lower(), "view_args": request.view_args}
    del kwargs['add_flask']

if 'add_request' in kwargs:
    extra['request'] = {
        "content_length": request.environ.get("CONTENT_LENGTH"),
        "content_type": request.environ.get("CONTENT_TYPE"),
        "method": request.environ.get("REQUEST_METHOD"),
        "path_info": request.environ.get("PATH_INFO"),
        "query_string": request.environ.get("QUERY_STRING"),
        "remote_addr": request.environ.get("REMOTE_ADDR"),
        "headers": dict(
            (key[5:].replace("-", "_").lower(), value)
            for key, value in request.environ.items()
            if key.startswith("HTTP_") and key.lower() not in ("http_cookie",)
        ),
    }
    del kwargs['add_request']
```

## 💡 Ideas for improvements

- [ ] Make the schema configurable with config
- [ ] Add middleware so as to log response as well (like the graylog extension)
- [ ] Add decorator so as to enable log for a specific endpoint (with user request and response automatically added)