"""Test JsonItemsLocalStorage class."""

import unittest
from pathlib import Path

from json_items_handlers import JsonItemsLocalStorage


class TestJsonItemsLocalStorage(unittest.TestCase):
    """Test JsonItemsLocalStorage class."""

    @classmethod
    def setUpClass(cls):
        JsonItemsLocalStorage._file_dir = Path("../test/test_output")

    @classmethod
    def tearDownClass(cls):
        """Tear down class."""
        pass

    def setUp(self):
        """Set up test."""
        self.file_name = "project_not_exist.json"
        self.json_handler = JsonItemsLocalStorage(self.file_name)

    def tearDown(self):
        """Tear down test."""
        pass

    def test_read_json_file(self):
        """Test read_json_file method."""
        # Test case 1: Read existing file
        self.assertTrue(type(self.json_handler.read_json_file()) is dict)

        # Test case 2: Read non-existing file
        self.assertEqual(self.json_handler.read_json_file(), {})
        # remove temporary file
        Path.unlink(self.json_handler.full_path)

    def test_save_to_json_file(self):
        """Test save_to_json_file method."""
        data = {"test": "test"}
        self.json_handler.save_to_json_file(data)
        self.assertEqual(self.json_handler.read_json_file(), data)
        # remove temporary file
        Path.unlink(self.json_handler.full_path)

    def test_append_to_json_file(self):
        """Test append_to_json_file method."""
        data = {"test": "test"}
        self.json_handler.save_to_json_file(data)
        data = {"test2": "test2"}
        self.json_handler.append_to_json_file(data)
        self.assertEqual(self.json_handler.read_json_file(), {"test": "test", "test2": "test2"})
        # remove temporary file
        Path.unlink(self.json_handler.full_path)
