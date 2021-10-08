"""Configure LDP logging handlers and middleware for your Flask app.
"""

import logging
import os
import time

from functools import wraps
from flask import (_request_ctx_stack, current_app, request, session, url_for,
                   has_request_context, g)
from logging_ldp.formatters import LDPGELFFormatter
from logging_ldp.handlers import LDPGELFTCPSocketHandler
from logging_ldp.schemas import LDPSchema
from marshmallow import fields, Schema
from werkzeug.local import LocalProxy


__version__ = "0.1.0"

current_user = LocalProxy(lambda: _get_user())

def _get_user():
    if not hasattr(current_app, 'login_manager'):
        return None

    if has_request_context() and not hasattr(_request_ctx_stack.top, 'user'):
        current_app.login_manager._load_user()

    return getattr(_request_ctx_stack.top, 'user', None)


class DefaultLoggingkSchema(LDPSchema):
    flask = fields.Raw()
    user = fields.Raw()
    response = fields.Raw()
    request = fields.Raw()
    data = fields.Raw()


def log_call(func):
    '''
    If you decorate a view with this, it will log to LDP the call.
    :param func: The view function to decorate.
    :type func: function
    '''
    @wraps(func)
    def decorated_view(*args, **kwargs):
        g.ldp_log_this_request = True
        try:
            # current_app.ensure_sync available in Flask >= 2.0
            return current_app.ensure_sync(func)(*args, **kwargs)
        except AttributeError:
            return func(*args, **kwargs)
    return decorated_view


class LDP(logging.Logger):
    __slots__ = ["app", "config", "handler"]

    def __init__(self, app=None, config=None, level=logging.NOTSET, extra=None):
        """
        Constructor for flask.ext.ldp.LDP

        :param app: Flask application to configure for ldp
        :type app: `flask.Flask` or `None`
        :param config: Configuration to use instead of `app.config`
        :type config: `dict` or `None`
        :param level: The logging level to set for this handler
        :type level: `int` or `str`
        :param extra: Additional LDP fields included in messages
        :type extra: `dict` or `None`
        """
        super(LDP, self).__init__(__name__, level=level)

        # Save their config for later
        self.config = config

        # If we have an app, then call `init_app` automatically
        if app is not None:
            self.init_app(app, self.config, extra)

    def init_app(self, app, config=None, extra=None):
        """
        Configure LDP logger from a Flask application

        Available configuration options:

          LDP_HOSTNAME - the host to send messages to [default: 'gra3.logs.ovh.com']
          LDP_TOKEN - the token needed to send logs [default: None]

        :param app: Flask application to configure this logger for
        :type app: flask.Flask
        :param config: An override config to use instead of `app.config`
        :type config: `dict` or `None`
        :param extra: Additional LDP fields included in messages
        :type extra: `dict` or `None`
        """
        # Use the config they provided
        if config is not None:
            self.config = config
        # Use the apps config if `config` was not provided
        elif app is not None:
            self.config = app.config
        self.app = app

        logging.warning(self.config)

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

        # Setup middleware if they asked for it
        self.setup_middleware()

    def setup_middleware(self):
        """Configure middleware to log each response"""
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)

    def before_request(self):
        """Middleware handler to record start time of each request"""
        # Record request start time, so we can get response time later
        g.ldp_start_time = time.time()

    def after_request(self, response):
        """Middleware helper to report each flask response to ldp"""
        # Only log what is asked
        if not hasattr(g, "ldp_log_this_request"):
            return response

        # Calculate the elapsed time for this request
        elapsed = 0
        if hasattr(g, "ldp_start_time"):
            elapsed = time.time() - g.ldp_start_time
            elapsed = int(round(1000 * elapsed))

        # Extra metadata to include with the message
        extra = {
            "flask": {"endpoint": str(request.endpoint).lower(), "view_args": request.view_args,},
            "response": {
                "headers": dict(
                    (key.replace("-", "_").lower(), value) for key, value in response.headers if key.lower() not in ("cookie",)
                ),
                "status_code": response.status_code,
                "time_ms": elapsed,
            },
            "request": {
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
            },
        }

        if current_user:
            log_user = {'id': current_user.get_id()}
            if hasattr(current_user, 'email'):
                log_user['email'] = current_user.email
            if hasattr(current_user, 'name'):
                log_user['name'] = current_user.name
            extra['user'] = log_user

        message = 'Finishing request for "%s %s" from %s' % (request.method, request.url, extra.get("remote_addr", "-"))
        if "user" in extra:
            logging.warning(extra['user'])
        self.info(message, extra=extra)

        # Always return the response
        return response
