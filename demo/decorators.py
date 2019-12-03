import logging
from typing import Any, Callable

from requests.exceptions import ConnectionError, HTTPError
from requests.models import Response
from requests.status_codes import codes
from tenacity import (
    RetryCallState,
    Retrying,
    stop_after_attempt,
    before_log,
    before_sleep_log,
)
from tenacity.retry import retry_if_exception, retry_if_exception_type
from tenacity.wait import wait_base, wait_random

SPOTIFY_DEFAULT_MAX_RETRIES = 10

retry_logger = logging.getLogger("spotify_retry")


def retry_if_network_error() -> retry_if_exception:
    return retry_if_exception_type(exception_types=(ConnectionError,))


def is_throttling_error(e: Exception) -> bool:
    if not isinstance(e, HTTPError):
        return False

    status_code = getattr(e.response, "status_code", None)
    if status_code is None:
        return False

    return status_code == codes.too_many_requests


def retry_if_throttling_error() -> retry_if_exception:
    return retry_if_exception(predicate=is_throttling_error)


class wait_spotify_throttling(wait_base):
    @staticmethod
    def get_wait_time_from_spotify_response(response: Response) -> int:
        seconds_to_wait_str = response.headers.get("Retry-After")

        try:
            seconds_to_wait = int(seconds_to_wait_str)
        except (TypeError, ValueError):
            # if the number of seconds to wait cannot be parsed from the response,
            # we choose to retry immediately
            seconds_to_wait = 0

        return seconds_to_wait

    def __call__(self, retry_state: RetryCallState) -> int:
        if retry_state.outcome.failed:
            e = retry_state.outcome.exception()
            if is_throttling_error(e):
                return self.get_wait_time_from_spotify_response(e.response)

        # if this is not a throttling issue, retry immediately
        return 0


def spotify_retry(max_retries: int = SPOTIFY_DEFAULT_MAX_RETRIES,) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            return Retrying(
                retry=(retry_if_network_error() | retry_if_throttling_error()),
                stop=stop_after_attempt(max_attempt_number=max_retries),
                wait=(wait_spotify_throttling() + wait_random(min=1, max=3)),
                before=before_log(retry_logger, logging.DEBUG),
                before_sleep=before_sleep_log(retry_logger, logging.WARNING),
            ).call(func, *args, **kwargs)

        return wrapper

    return decorator
