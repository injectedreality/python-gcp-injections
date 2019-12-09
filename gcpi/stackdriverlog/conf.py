# -*- coding: utf-8 -*-
"""
Settings for stackdriverlog are all namespaced in the
STACK_DRIVER_LOGGER setting. For example

STACK_DRIVER_LOGGER = {
    REQUEST_MIDDLEWARE_IGNORE_PATHS: [...],
    REQUEST_MIDDLEWARE_BODY_MAX_LENGTH: 500,
    REQUEST_MIDDLEWARE_SENSITIVE_POST_PARAMETERS: [...],
    LOGGING = {
        version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            ...
        },
        'handlers': {
            ...
        },
        ...
    }
}
"""
import collections
import logging.config

import structlog

from gcpi.stackdriverlog.contrib import compat
from gcpi.stackdriverlog.formatters import JsonProcessorFormatter


USER_SETTINGS = None
if compat.django_support:
    from django.core.exceptions import ImproperlyConfigured
    try:
        from django.conf import settings
        USER_SETTINGS = getattr(settings, 'STACK_DRIVER_LOGGER', {})

        if 'LOGGING' not in USER_SETTINGS and settings.LOGGING:
            USER_SETTINGS['LOGGING'] = settings.LOGGING
    except ImproperlyConfigured:
        # Might trigger if Django is installed, but not properly set ut.
        # We don't want to break here as we could potentially be running
        # from a shell script or other things that want to log.
        import warnings
        warnings.warn('Django is installed, but not properly set up!')


DEFAULTS = {
    # List of regular expressions that should be ignored
    # by the logging middleware (Django only for now).
    'REQUEST_MIDDLEWARE_IGNORE_PATHS': [
        r'^/health/?$'
    ],

    # List of json keys in request body that should not be
    # logged by the logging middleware (Django only for now)
    'REQUEST_MIDDLEWARE_SENSITIVE_POST_PARAMETERS': ['password', 'token'],

    # Truncate and log body as string if body is too long
    'REQUEST_MIDDLEWARE_BODY_MAX_LENGTH': 500,

    # If set True, force settings all log levels to DEBUG.
    'FORCE_DEBUG_LEVEL': False,

    # Python logging dict config
    'LOGGING': {
        'version': 1,
        'disable_existing_loggers': True,
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        },
        'formatters': {
            'json': {
                '()': JsonProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(colors=False),
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'json'
            },
        }
    }
}


class Settings:
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS

        # Setup logging.
        # Defaults taken from structlog documentation.
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # If we're forcing DEBUG log level using the FORCE_DEBUG_LEVEL setting,
        # update the config before passing it.
        if self.FORCE_DEBUG_LEVEL is True:
            self.__set_force_debug__(self.LOGGING)

        logging.config.dictConfig(self.LOGGING)

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid setting: '%s'" % attr)

        try:
            value = self.user_settings[attr]
        except KeyError:
            value = self.defaults[attr]

        # Cache the setting
        setattr(self, attr, value)
        return value

    def __set_force_debug__(self, config):
        for key, value in config.items():
            if isinstance(value, collections.Mapping):
                self.__set_force_debug__(value)
            elif key == 'level':
                config[key] = 'DEBUG'

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = {}
        return self._user_settings


settings = Settings(USER_SETTINGS, DEFAULTS)


def load_settings(*args, **kwargs):
    global settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'STACK_DRIVER_LOGGER':
        settings = Settings(value, DEFAULTS)
    elif (compat.django_support or compat.flask_support) and setting == 'LOGGING':
        settings = Settings({'LOGGING': value}, DEFAULTS)
