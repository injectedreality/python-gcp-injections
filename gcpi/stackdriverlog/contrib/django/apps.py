from django.apps import AppConfig
from django.core.signals import setting_changed

from gcpi.stackdriverlog.conf import load_settings

print("Loaded StackDriverLoggerConfig file")
class StackDriverLoggerConfig(AppConfig):
    name = 'gcpi.stackdriverlog'

    def ready(self):
        # Connect the settings_changed signal so that we can
        # pick up changes from django settings.
        setting_changed.connect(load_settings)
