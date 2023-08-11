import logging

from . import local


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(local, "request_id", "none")
        return True
