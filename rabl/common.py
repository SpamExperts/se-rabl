"""Common utility methods."""

import logging

import raven
import raven.transport
from raven.handlers.logging import SentryHandler


SENTRY_IGNORES = [
    "KeyboardInterrupt",
    "MemoryError",
]


def setup_logging(logger, filename=None, sentry=None, application=None,
                  stream_level=None):
    """Initialize logging for this logger.

    :param logger: The logger that should be initialized.
    :param filename: The filename.
    :param sentry: If specified also add a SentryHandler
    :param stream_level: If specified add a stream handler
      and set it to that level
    """
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    logger.setLevel(logging.DEBUG)

    if filename:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)

    if stream_level is not None:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(getattr(logging, stream_level))
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if sentry:
        client = raven.Client(sentry,
                              enable_breadcrumbs=False,
                              ignore_exceptions=SENTRY_IGNORES,
                              transport=raven.transport.HTTPTransport)
        sentry_handler = SentryHandler(client)
        sentry_handler.setLevel(logging.WARNING)
        logger.addHandler(sentry_handler)
        null_loggers = [
            logging.getLogger("sentry.errors"),
            logging.getLogger("sentry.errors.uncaught")
        ]
        for null_logger in null_loggers:
            null_logger.handlers = [logging.NullHandler()]
