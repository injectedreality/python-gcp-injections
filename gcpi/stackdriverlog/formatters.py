# -*- coding: utf-8 -*-
import re
import json
import traceback
import time
from collections import OrderedDict
from datetime import date, datetime, time as dt_time
from functools import partial
from inspect import istraceback
from itertools import chain

from structlog.stdlib import ProcessorFormatter
from structlog.processors import format_exc_info

# http://docs.python.org/library/logging.html#logrecord-attributes
RESERVED_ATTRS = (
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module',
    'msecs', 'message', 'msg', 'name', 'pathname', 'process',
    'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName')


class JsonEncoder(json.JSONEncoder):
    """
    Extended JsonEncoder for logging purposes.

    Shamelessly stolen from
    https://github.com/madzak/python-json-logger/blob/master/src/pythonjsonlogger/jsonlogger.py
    """
    def default(self, obj):
        if isinstance(obj, (date, datetime, dt_time)) or (
                hasattr(obj, 'isoformat') and callable(obj.isoformat)):
            return self.format_datetime_obj(obj)

        elif istraceback(obj):
            return ''.join(traceback.format_tb(obj)).strip()

        elif type(obj) == (Exception or isinstance(obj, Exception) or type(obj) == type):
            return str(obj)

        try:
            return super(JsonEncoder, self).default(obj)

        except TypeError:
            try:
                return str(obj)

            except Exception:
                return None

    @staticmethod
    def format_datetime_obj(obj):
        return obj.isoformat()


class JsonProcessorFormatter(ProcessorFormatter):
    """
    A structlog formatter that format stdlib log messages as json strings,
    before they are processed by structlog.

    :param json_default: a function for encoding non-standard objects
      as outlined in http://docs.python.org/3/library/json.html
    :param json_encoder: optional custom encoder
    :param json_serializer: a :meth:`json.dumps`-compatible callable
      that will be used to serialize the log record.
    :param prefix: an optional string prefix added at the beginning of
      the formatted string
    """
    default_time_format = '%Y-%m-%dT%H:%M:%S'

    def __init__(self, processor, foreign_pre_chain=None,
                 keep_exc_info=False, keep_stack_info=False, *args, **kwargs):

        self.json_default = kwargs.pop('json_default', None)
        self.json_encoder = kwargs.pop('json_encoder', None)
        self.json_serializer = kwargs.pop('json_serializer', json.dumps)
        self.json_indent = kwargs.pop('json_indent', None)
        self.prefix = kwargs.pop('prefix', '')

        if not self.json_encoder and not self.json_default:
            self.json_encoder = JsonEncoder

        # Default to UTC timestamps
        self.converter = kwargs.pop('converter', time.gmtime)
        if 'datefmt' not in kwargs:
            kwargs['datefmt'] = '%Y-%m-%dT%H:%M:%S%z'

        super(JsonProcessorFormatter, self).__init__(processor, foreign_pre_chain,
                                                     keep_exc_info, keep_stack_info, *args, **kwargs)

    @property
    def required_fields(self):
        pattern = re.compile(r'\((.+?)\)', re.IGNORECASE)
        return set(chain(pattern.findall(self._fmt), ['level', 'logger', 'timestamp']))

    def add_fields(self, record, messages):
        """
        Add all required fields to the log record.
        """
        # Key is desired field name in the output, and value
        # is a two tuple with the lookup attribute and either a function
        # to run the value through or None. If not value is found and a function
        # is provided it wil be called without any arguments.
        field_aliases = {
            'event': ('message', None),
            'level': ('levelname', str.lower),
            'logger': ('name', None),
            'timestamp': (None, partial(self.formatTime, record=record, datefmt=self.datefmt))
        }

        log_record = OrderedDict()
        for field in self.required_fields:
            alias, proc = field_aliases.get(field, (None, None))
            value = record.__dict__.get(alias or field)
            if value:
                log_record[field] = proc(value) if proc else value
            elif proc:
                log_record[field] = proc()

        log_record.update(messages)
        for key, value in record.__dict__.items():
            if key not in RESERVED_ATTRS and not (hasattr(key, 'startswith') and key.startswith('_')):
                log_record[key] = value

        log_record['severity'] = log_record.pop('level','info').upper()
        if not 'message' in log_record:
            log_record['message'] = log_record.get('event')
        log_record.pop('timestamp', None)

        return log_record

    def format(self, record):
        """
        Converts the log records message to a dictionary and
        pass it on to the ``structlog.stdlib.ProcessorFormatter`` to
        do its magic.
        """
        # Make sure message always is a dictionary
        message = record.getMessage()
        try:
            message = json.loads(message)
        except json.JSONDecodeError:
            message = {'event': message}

        # Format exceptions to JSON and set `exc_info` to None in order
        # to avoid the stdlib logger to write it out.
        if record.exc_info and 'exc_info' not in message:
            message.update(**format_exc_info(
                None, record.levelname,
                {'exc_info': record.exc_info, 'event': record.getMessage()}
            ))
            record.exc_info = None

        record.msg = self.json_serializer(self.add_fields(record, message), default=self.json_default,
                                          cls=self.json_encoder, indent=self.json_indent)

        # We're done formatting the `record.msg` attribute.
        # Need to delete `record.args` so that `record.getMessage()`
        # don't raise any errors.
        record.args = ()
        return super(JsonProcessorFormatter, self).format(record)
