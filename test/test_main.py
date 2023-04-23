"""Test cases for main.py."""

import unittest
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from main import get_all_items_to_check, scrap_single_item


def test_scrap_single_item(single_item_html_source, json_project_settings):
    """Test scrap_single_item function."""
    soup = BeautifulSoup(single_item_html_source, "lxml")
    sku, product_dict = scrap_single_item(soup, json_project_settings["modules"][0])

    assert sku == "LV II.7.180.47.5.B"
    assert product_dict[sku]["price"] == "14 990 грн"
    assert product_dict[sku]["stock"] == "В наявності"


def test_get_all_items_to_check(items_container_html_source, mock_project_object):
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
    # Test case 4: Return empty list when no items are found in the container
    all_items = get_all_items_to_check(
        items_container_html_source, mock_project_object, 0
    )
    assert len(all_items) == 0


def test_get_all_items_to_check_single_page(single_page_html_source, mock_project_object_single_page):
    """Test get_all_items_to_check function with single_url."""
    all_items = get_all_items_to_check(
        single_page_html_source, mock_project_object_single_page, 1
    )
    assert len(all_items) == 1

