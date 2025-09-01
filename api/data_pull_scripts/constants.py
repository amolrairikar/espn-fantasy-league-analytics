"""Constant values across all requests to ESPN Fantasy Football API."""

from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter

POST_2024_BASE_URL = "https://lm-api-reads.fantasy.espn.com/apis/v3/games"
X_FANTASY_FILTER_HEADER = '{"players":{"limit":1500,"sortAppliedStatTotal":{"sortAsc":false,"sortPriority":2,"value":"002024"}}}'

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
