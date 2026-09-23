import logging
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

class AuthClient:
    def __init__(self, base_url, timeout=3, logger=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

    def current_username(self, cookie_header):
        if not self.base_url or not cookie_header:
            return "guest"
        try:
            request = Request(
                f"{self.base_url}/api/session-user", headers={"Cookie": cookie_header}
            )
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            username = payload.get("username")
            if isinstance(username, str) and username.strip() and username != "guest":
                return username.strip().lower()
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
            self.logger.exception("Unable to validate the Byteon session")
        return "guest"
