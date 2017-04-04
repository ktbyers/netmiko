from requests.exceptions import ConnectTimeout
from requests.exceptions import HTTPError


class NetMikoRequestsTimeoutException(ConnectTimeout):
    """Json request timed out"""
    pass


class NetMikoRequestsHTTPException(HTTPError):
    """HTTP status code was a 4XX client error or 5XX server error response"""
    pass