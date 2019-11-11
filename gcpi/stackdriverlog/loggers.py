import sys
import logging
import logging.config
import structlog

from gcpi.stackdriverlog.conf import settings


class StackDriverLogger(logging.Logger):

    def __init__(self, config=None, *args, **kwargs):
        kwargs.setdefault('name', 'default')
        super(StackDriverLogger, self).__init__(*args, **kwargs)

        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=True),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]

        logging.config.dictConfig(config or settings.DEFAULT_CONFIG)
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        def exc_handler(excType, excValue, traceback):
            structlog.getLogger().exception('uncaught-exception',
                                            exc_info=(excType, excValue, traceback))
        sys.excepthook = exc_handler

    def get_logger(self, name=None):
        return structlog.getLogger(name)
