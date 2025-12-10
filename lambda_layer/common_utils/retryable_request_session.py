"""Common request session configuration with retries enabled."""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session() -> requests.Session:
    """
    Creates a requests session with a configured retry strategy.

    Returns:
        requests.Session: A session object with retry capability. Allows
            for 3 retries for statuses in status_forcelist.
    """
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
