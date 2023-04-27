"""Test cases for main.py."""

import unittest
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from main import (
    check_changes,
    get_all_items_to_check,
    get_url_response,
    scrap_single_item,
)


def test_scrap_single_item(single_item_html_source, json_project_settings):
    """Test scrap_single_item function."""
    soup = BeautifulSoup(single_item_html_source, "lxml")
    sku, product_dict = scrap_single_item(soup, json_project_settings["modules"][0])

    assert sku == "LV II.7.180.47.5.B"
    assert product_dict[sku]["price"] == "14 990 грн"
    assert product_dict[sku]["stock"] == "В наявності"


class TestGetAllItemsToCheck:
    """Test cases for get_all_items_to_check function."""

    def test_get_all_items_to_check(
        self, items_container_html_source, mock_project_object
    ):
        """Test get_all_items_to_check function."""
        # Test case 1: Get all items when container is specified with tag and class
        all_items = get_all_items_to_check(
            items_container_html_source, mock_project_object, 0
        )
        assert len(all_items) == 24
        # Test case 2: Get all items when container is specified with selector
        all_items = get_all_items_to_check(
            items_container_html_source, mock_project_object, 0
        )
        assert len(all_items) == 24
        # Test case 4: Return empty list when no items are found in the container and mock send_email
        with patch("main.send_email") as send_email_mock:
            all_items = get_all_items_to_check(
                items_container_html_source, mock_project_object, 0
            )
        assert len(all_items) == 0
        assert send_email_mock.called

    def test_get_all_items_to_check_single_page(
        self, single_page_html_source, mock_project_object_single_page
    ):
        """Test get_all_items_to_check function with single_url."""
        all_items = get_all_items_to_check(
            single_page_html_source, mock_project_object_single_page, 1
        )
        assert len(all_items) == 1


class TestGetUrlResponse(unittest.TestCase):
    """Test cases for get_url_response function."""

    def setUp(self):
        """Set up test case."""
        self.request_mock = MagicMock()
        self.request_delay = 1
        self.module_with_paginator = {
            "paginator_pattern": "https://example.com?page=$page",
            "paginator_count": 3,
            "single_url": None,
        }
        self.module_without_paginator = {
            "paginator_pattern": None,
            "paginator_count": None,
            "single_url": "https://example.com",
        }

    def test_get_url_response_with_paginator(self):
        """Test get_url_response function with paginator."""
        self.request_mock.read_url.side_effect = [
            MagicMock(status_code=200),
            MagicMock(status_code=404),
            MagicMock(status_code=200),
        ]
        expected_response = MagicMock(status_code=404)
        actual_response = get_url_response(
            module=self.module_with_paginator,
            request=self.request_mock,
            request_delay=self.request_delay,
        )
        self.assertEqual(actual_response.status_code, expected_response.status_code)

    def test_get_url_response_without_paginator(self):
        """Test get_url_response function without paginator."""
        self.request_mock.read_url.return_value = MagicMock(status_code=200)
        expected_response = MagicMock(status_code=200)
        actual_response = get_url_response(
            module=self.module_without_paginator,
            request=self.request_mock,
            request_delay=self.request_delay,
        )
        self.assertEqual(actual_response.status_code, expected_response.status_code)


class TestCheckChanges(unittest.TestCase):
    def setUp(self):
        self.source = "https://example.com"
        self.project_settings = MagicMock()
        self.module_index = 0
        self.items_list_instance = MagicMock()
        self.items_list_instance.read_json_file.return_value = {
            "val1": {"sku": "val1"},
            "val2": {"sku": "val2"},
        }

    def test_check_changes_no_changes(self):
        """Test check_changes function with no changes."""
        items_to_check = ["item1"]
        get_all_items_to_check_mock = MagicMock(return_value=items_to_check)
        scrap_single_item_mock = MagicMock(
            return_value=("val1", {"val1": {"sku": "val1"}})
        )

        with patch("main.get_all_items_to_check", get_all_items_to_check_mock), patch(
            "main.scrap_single_item", scrap_single_item_mock
        ):
            result = check_changes(
                self.source,
                self.items_list_instance,
                self.project_settings,
                self.module_index,
            )

        self.assertEqual(len(result), 0)
        self.items_list_instance.read_json_file.assert_called_once()

    def test_check_changes_with_changes(self):
        """Test check_changes function with changes."""
        self.items_list_instance.read_json_file.return_value = {
            "val1": {"sku": "val1"},
            "val2": {"sku": "val2"},
        }
        items_to_check = ["item1", "item2"]
        get_all_items_to_check_mock = MagicMock(return_value=items_to_check)
        scrap_single_item_mock = MagicMock(
            return_value=("val1", {"val1": {"sku": "new_value"}})
        )

        with patch("main.get_all_items_to_check", get_all_items_to_check_mock), patch(
            "main.scrap_single_item", scrap_single_item_mock
        ):
            result = check_changes(
                self.source,
                self.items_list_instance,
                self.project_settings,
                self.module_index,
            )
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], {"sku": "new_value"})
        self.items_list_instance.read_json_file.assert_called_once()

    def test_check_changes_new_product(self):
        """Test check_changes function with new product."""
        items_to_check = ["item1"]
        get_all_items_to_check_mock = MagicMock(return_value=items_to_check)
        scrap_single_item_mock = MagicMock(
            return_value=("sku3", {"sku3": {"sku": "sku3"}})
        )

        with patch("main.get_all_items_to_check", get_all_items_to_check_mock), patch(
            "main.scrap_single_item", scrap_single_item_mock
        ):
            result = check_changes(
                self.source,
                self.items_list_instance,
                self.project_settings,
                self.module_index,
            )
        self.assertEqual(len(result), 1)
        self.assertDictEqual(result[0], {"sku": "sku3"})
        self.items_list_instance.read_json_file.assert_called_once()
        self.items_list_instance.append_to_json_file.assert_called_once_with(
            data={"sku3": {"sku": "sku3"}}
        )
