"""Common utility methods."""

import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


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
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.WARNING
        )
        integrations = [sentry_logging]
        sentry_sdk.init(
            dsn=sentry,
            integrations=integrations
        )
