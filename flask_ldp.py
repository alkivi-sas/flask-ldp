"""Configure LDP logging handlers and middleware for your Flask app.
"""

import logging
import os

from flask import request
from logging_ldp.formatters import LDPGELFFormatter
from logging_ldp.handlers import LDPGELFTCPSocketHandler
from logging_ldp.schemas import LDPSchema
from marshmallow import fields


__version__ = "0.1.1"


class DefaultLoggingkSchema(LDPSchema):
    user = fields.Raw()
    data = fields.Raw()
    flask = fields.Raw()
    request = fields.Raw()
    response = fields.Raw()


class LDP(logging.Logger):
    __slots__ = ["app", "config", "handler"]

    def __init__(self, app=None, config=None, level=logging.NOTSET):
        """
        Constructor for flask.ext.ldp.LDP

        :param app: Flask application to configure for ldp
        :type app: `flask.Flask` or `None`
        :param config: Configuration to use instead of `app.config`
        :type config: `dict` or `None`
        :param level: The logging level to set for this handler
        :type level: `int` or `str`
        """
        super(LDP, self).__init__(__name__, level=level)

        # Save their config for later
        self.config = config

        # If we have an app, then call `init_app` automatically
        if app is not None:
            self.init_app(app, self.config)

    def init_app(self, app, config=None):
        """
        Configure LDP logger from a Flask application

        Available configuration options:

          LDP_HOSTNAME - the host to send messages to [default: 'gra3.logs.ovh.com']
          LDP_TOKEN - the token needed to send logs [default: None]

        :param app: Flask application to configure this logger for
        :type app: flask.Flask
        :param config: An override config to use instead of `app.config`
        :type config: `dict` or `None`
        """
        # Use the config they provided
        if config is not None:
            self.config = config
        # Use the apps config if `config` was not provided
        elif app is not None:
            self.config = app.config
        self.app = app

        # Setup default config settings
        default_hostname = os.environ.get('LDP_HOSTNAME', 'gra3.logs.ovh.com')
        default_token = os.environ.get('LDP_TOKEN', None)
        self.config.setdefault("LDP_HOSTNAME", default_hostname)
        self.config.setdefault("LDP_TOKEN", default_token)

        # No token : warning
        if self.config["LDP_TOKEN"] is None:
            logging.warning("No LDP_TOKEN defined, will not send any log")
            return

        # Configure the logging handler and attach to this logger
        handler = LDPGELFTCPSocketHandler(hostname=self.config["LDP_HOSTNAME"])

        formatter = LDPGELFFormatter(token=self.config["LDP_TOKEN"], schema=DefaultLoggingkSchema)
        handler.setFormatter(formatter)

        self.handler = handler
        self.addHandler(self.handler)

    def _log(self, level, msg, *args, **kwargs):

        extra = kwargs.get('extra', {})

        if 'add_flask' in kwargs and kwargs['add_flask']:
            extra['flask'] = {"endpoint": str(request.endpoint).lower(), "view_args": request.view_args}
            del kwargs['add_flask']

        if 'add_request' in kwargs and kwargs['add_request']:
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

        kwargs['extra'] = extra
        super()._log(level, msg, *args, **kwargs)
