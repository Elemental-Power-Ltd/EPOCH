import datetime
import logging
import sys
from pathlib import Path
from typing import Any, cast

LOG_DIR = Path("logs", "optimisation_service")


class EndpointFilter(logging.Filter):
    """Filter out logs for a specific method, matching a specific path."""

    def __init__(
        self,
        endpoint_path: str,
        request_method: str,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Construct the filter by specifying an endpoint path and a HTTP request method.

        Filters out all successful calls with the specified request method and the endpoitn path.

        Parameters
        ----------
        endpoint_path
            Path to the endpoint you want to filter out, e.g. "/queue-status"
        request_method
            HTTP
        """
        super().__init__(*args, **kwargs)
        self._endpoint_path = endpoint_path

        self._request_method = request_method

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Check if we should we allow this record through the filter.

        Checks if the request method matches the specified request method and that the endpoint path matches.

        Returns
        -------
            True if we should allow this record through, False if otherwise.
        """
        if not isinstance(record.args, tuple | list) or len(record.args) < 4:
            return True
        request_method = str(record.args[1])  # should be GET or POST
        query_string = str(record.args[2])  # complete query string (so parameter and other value included)
        _ = record.args[3]  # HMTL version
        try:
            status_code = int(cast(str, record.args[4]))
        except ValueError:
            return True

        # Only eat successful records, so let all errors through.
        if status_code != 200:
            return True

        # Only filter out those that match the path and the request method
        request_method_matches = request_method == self._request_method
        path_matches = self._endpoint_path in query_string

        return not (request_method_matches and path_matches)


def configure_logging() -> None:
    """
    Set up logging.

    This involves pointing it do a directory, and adding file handlers as well as any filters required.

    Returns
    -------
    None
    """
    LOG_DIR.mkdir(exist_ok=True, parents=True)
    formatter_file = logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    formatter_stream = logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler_file = logging.FileHandler(LOG_DIR / f"{datetime.datetime.now(datetime.UTC).strftime('%Y_%m_%d_%H_%M_%S')}.log")
    handler_stream = logging.StreamHandler(sys.stdout)
    handler_file.setFormatter(formatter_file)
    handler_stream.setFormatter(formatter_stream)

    logger = logging.getLogger("default")
    logger.setLevel(logging.DEBUG)

    logger.addHandler(handler_file)
    logger.addHandler(handler_stream)

    # Use this to squish the uvicorn "queue-status" logs
    uvicorn_logger = logging.getLogger("uvicorn.access")
    uvicorn_logger.addFilter(EndpointFilter(endpoint_path="/queue-status", request_method="POST"))
