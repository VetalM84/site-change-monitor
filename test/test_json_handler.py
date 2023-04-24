"""Test JsonHandler class."""

import unittest
from pathlib import Path

from json_items_handlers import JsonHandler


class TestJsonHandler(unittest.TestCase):
    """Test JsonHandler class."""

    @classmethod
    def setUpClass(cls):
        JsonHandler._file_dir = Path("test/fixtures")

    @classmethod
    def tearDownClass(cls):
        """Tear down class."""
        pass

    def setUp(self):
        """Set up test."""
        self.file_name = "test.json"
        self.json_handler = JsonHandler(self.file_name)

    def tearDown(self):
        """Tear down test."""
        pass

    def test_set_full_path(self):
        """Test set_full_path method."""
        file_path = Path(JsonHandler._file_dir) / self.file_name
        self.assertEqual(self.json_handler.set_full_path(), file_path)
