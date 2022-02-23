import json
import logging

from logstash.formatter import LogstashFormatterBase
from rest_framework.views import exception_handler

from kallisticore.utils import threadlocals

_logger = logging.getLogger(__name__)


class KallistiLogStashFormatter(LogstashFormatterBase):
    """
    Kallisti will use stream_handler to print log
    """

    def format(self, record: logging.LogRecord):
        """
         This formatter will only work with default django format which is
         "METHOD URI HTTP_PROTOCOL" Format in message field.
         It's same as LogstashFormatterVersion1, but 'path' will be URI and
         type will be method type.
        """

        message_type = ''
        uri_path = record.pathname

        # django default log message is "METHOD PATH http_version",
        # use method/path to replace message_type to method, uri_path to path
        if record.name == "django.server" and len(record.args) > 0:
            token = record.args[0].split(' ')
            if len(token) == 3:
                message_type = token[0]
                uri_path = token[1]

        message = {
            '@timestamp': self.format_timestamp(record.created),
            '@version': '1',
            'message': record.getMessage(),
            'host': self.host,
            'path': uri_path,
            'tags': self.tags,
            'type': message_type,
            'level': record.levelname,
            'logger_name': record.name,
        }

        user_id = threadlocals.ThreadLocal.get_attr("user_id", None)
        if user_id:
            message["user_id"] = user_id

        message.update(self.get_extra_fields(record))

        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return json.dumps(message)


def kallisti_exception_handler(exc, context):
    _logger.exception("%s %s" % (exc, context))
    return exception_handler(exc, context)
