# -*- coding: utf-8 -*-
"""
Settings for stackdriverlog are all namespaced in the
STACK_DRIVER_LOGGER setting. For example

STACK_DRIVER_LOGGER = {
    DEFAULT_CONFIG = {
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
import structlog

USER_SETTINGS = None
DEFAULTS = {
    'DEFAULT_CONFIG': {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'debug': {
                'format': '%(module)s.%(funcName)s: %(message)s'
            },
            'plain': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(colors=False),
            },
            'colored': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.dev.ConsoleRenderer(colors=True),
                "foreign_pre_chain": [
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt='iso')
                ],
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'plain'
            },
        },
        'loggers': {
            'default': {
                'level': 'INFO',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}


class Settings:
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError('Invalid setting: \'%s\'' % attr)

        try:
            value = self.user_settings[attr]
        except KeyError:
            value = self.defaults[attr]

        # Cache the setting
        setattr(self, attr, value)
        return value

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = {}
        return self._user_settings


settings = Settings(USER_SETTINGS, DEFAULTS)


def reload_settings(*args, **kwargs):
    global settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'STACK_DRIVER_LOGGER':
        settings = Settings(value, DEFAULTS)
