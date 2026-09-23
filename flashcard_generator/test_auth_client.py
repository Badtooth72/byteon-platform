import unittest
from unittest.mock import Mock, patch

from auth_client import AuthClient


class AuthClientTests(unittest.TestCase):
    @patch("auth_client.urlopen")
    def test_uses_central_session_identity(self, urlopen):
        response = Mock()
        response.read.return_value = b'{"username": "AGriffiths"}'
        urlopen.return_value.__enter__.return_value = response
        self.assertEqual(AuthClient("http://auth").current_username("sid=1"), "agriffiths")

    def test_missing_cookie_is_guest(self):
        self.assertEqual(AuthClient("http://auth").current_username(""), "guest")


if __name__ == "__main__":
    unittest.main()
