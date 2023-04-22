"""Test cases for main.py."""

import unittest
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup

from main import scrap_single_item


def test_scrap_single_item(single_item_html_source, json_project_settings):
    """Test scrap_single_item function."""
    soup = BeautifulSoup(single_item_html_source, "lxml")
    sku, product_dict = scrap_single_item(soup, json_project_settings["modules"][0])

    assert sku == "LV II.7.180.47.5.B"
    assert product_dict[sku]["price"] == "14 990 грн"
    assert product_dict[sku]["stock"] == "В наявності"
