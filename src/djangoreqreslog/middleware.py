"""
Middleware to log `*/api/*` requests and responses.
"""
import json
import logging
import time
import uuid

from filters import local

request_logger = logging.getLogger(__name__)


EXCLUDE_REQUEST_PATHS = [
    "/v1/user_identifiers/household_logs/",
    "/v1/ip/",
    "/v1/health/",
    "/v1/inventories/retool/",
]


class RequestResponseLogMiddleware:
    """Request Response Logging Middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4().hex
        local.request_id = request_id
        request.id = request_id

        start_time = time.time()

        request_path = str(request.get_full_path())

        log_data = {
            "request_method": request.method,
            "request_path": request_path,
        }

        # Only logging "*/api/*" patterns
        if "/api/" in request_path and not any(
            [path in request_path for path in EXCLUDE_REQUEST_PATHS]
        ):
            try:
                if request.body:
                    if request.META.get("CONTENT_TYPE") == "application/json":
                        log_data["request_body"] = json.loads(
                            request.body.decode("utf-8").strip()
                        )
                    elif "multipart/form-data;" in request.META.get("CONTENT_TYPE"):
                        log_data["request_body"] = "some-form-data"
                    elif request.META.get("CONTENT_TYPE") == "text/plain":
                        log_data["request_body"] = "some-text-data"
                    else:
                        log_data["request_body"] = "some-other-data"
                else:
                    log_data["request_body"] = ""
            except Exception as e:
                log_data["request_body"] = "err - " + str(e)

        # request passes on to controller
        response = self.get_response(request)

        # add runtime to our log_data
        if "/api/" in request_path and not any(
            [path in request_path for path in EXCLUDE_REQUEST_PATHS]
        ):
            try:
                if response and response.content:
                    log_data["response_body"] = json.loads(
                        response.content.decode("utf-8")
                    )
                else:
                    log_data["response_body"] = response.content.decode("utf-8")
            except Exception as e:
                log_data["response_body"] = "err - " + str(e)

            log_data["run_time"] = time.time() - start_time

            request_logger.info(msg=log_data)

        return response

    # Log unhandled exceptions as well
    def process_exception(self, request, exception):
        try:
            raise exception
        except Exception as e:
            request_logger.exception("Unhandled Exception: " + str(e))
        return exception
