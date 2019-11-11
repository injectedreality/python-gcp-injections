# -*- coding: utf-8 -*-
try:
    from flask.signals import appcontext_pushed, signals_available
except ImportError:
    # Flask not supported because it is not imported
    signals_available = False


from gcpi.stackdriverlog.conf import load_settings


def signal_handler(sender, **kwargs):
    """
    Signals receiver for ``flask.appcontext_pushed`` signal.
    Get ``STACK_DRIVER_LOGGER`` namespace from flask app config, and
    reload the settings used to instantiate the ``StackDriverLogger`` class.
    """
    user_settings = sender.config.get('LOGGING', None)
    load_settings(setting='LOGGING', value=user_settings)


if signals_available:
    # If the ``blinker`` library is installed,
    # connect the signal to the signal handler.
    appcontext_pushed.connect(signal_handler)
