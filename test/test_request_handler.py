"""Test cases for RequestHandler class and methods."""

import unittest
from unittest.mock import MagicMock, patch

from main import RequestHandler


class TestRequestHandler(unittest.TestCase):
    """Test cases for RequestHandler class."""

    def setUp(self):
        """Setup method."""
        self.handler = RequestHandler()
        self.mock_response = MagicMock()

    def tearDown(self):
        """Tear down method."""
        pass

    @patch("main.requests.get")
    @patch("main.time.sleep")
    def test_read_url(self, mock_sleep, mock_requests_get):
        """Test read_url method."""
        url = "https://example.com"
        delay = 1
        response_text = "<html><body>Hello World!</body></html>"

        self.mock_response.text = response_text
        mock_requests_get.return_value = self.mock_response

        response = self.handler.read_url(url, delay)

        mock_sleep.assert_called_once_with(delay)
        self.assertEquals(response.text, response_text)

    def test_set_headers(self):
        """Test set_headers method."""
        headers = {"Content-Type": "text/html", "Cache-Control": "no-cache"}
        self.handler.set_headers(headers)
        assert self.handler._RequestHandler__headers == headers
