"""Main file to """

import json
import time
from pathlib import Path
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from icecream import ic
from requests import Response

from mail import send_email


class RequestHandler:
    """Class to work with requests."""

    def __init__(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/111.0.0.0 Safari/537.36"
        }
        self._headers = headers

    def set_headers(self, headers: dict) -> None:
        """Set headers."""
        self._headers = headers

    def read_url(self, url: str, delay: int = 0) -> Response:
        """Read url and return response. Delay is in seconds."""
        response = requests.get(url, headers=self._headers)
        time.sleep(delay)
        return response


class JsonHandler:
    """Class to work with json files."""

    def __init__(self, file_dir: str, file_name: str):
        self._file_dir = file_dir
        self._file_name = file_name
        self.full_path = self.set_full_path()

    def set_full_path(self) -> Path:
        """Set ful path file dir."""
        folder_path = Path(self._file_dir)
        file_path = Path(self._file_name)
        return folder_path / file_path

    def read_json_file(self) -> dict:
        """Read json file."""
        with open(self.full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data


class JsonItemsHandler(JsonHandler):
    """Class to work with json files with items."""

    def __init__(self, file_dir: str, file_name: str):
        super().__init__(file_dir, file_name)

    def save_to_json_file(self, data) -> None:
        """Save data to json file."""
        with open(self.full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def append_to_json_file(self, data) -> None:
        """Append data to json file."""
        existing_data = self.read_json_file()
        existing_data.update(data)
        with open(self.full_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)


def save_html_file(file_name, response, counter=0) -> None:
    """Save html file."""
    with open(f"data/{file_name}_{counter}.html", "w", encoding="utf-8") as f:
        f.write(response.text)


def read_html_file(file_name: str) -> str:
    """Read html file."""
    with open(f"data/{file_name}.html", "r", encoding="utf-8") as f:
        src = f.read()
    return src


def scrap_links(source, link_css_class: str, domain: str) -> list:
    """Scrap links."""
    links = []
    soup = BeautifulSoup(source, "lxml")

    for link_tag in soup.findAll("a", {"class": link_css_class}):
        links.append(domain + link_tag.get("href"))

    return links


def scrap_single_item(source) -> Tuple[str, dict]:
    """Scrap product data for single product for arttidesign."""
    product_dict = {}

    product_name = source.find("a", {"class": "cs-goods-title"}).text.strip()
    # ic(product_name)
    product_link = source.find("a", {"class": "cs-goods-title"}).get("href")
    # ic(product_link)
    product_price = source.find(
        "span",
        {"class": "cs-goods-price__value cs-goods-price__value_type_current"},
    ).text.strip()
    # ic(product_price)
    product_sku = (
        source.find("span", {"class": "cs-goods-sku"}).text.strip().replace("Код: ", "")
    )
    # ic(product_sku)
    product_stock = source.find(
        "div", {"class": "cs-goods-data cs-product-gallery__data"}
    ).text.strip()
    # ic(product_stock)

    product_dict[product_sku] = {
        "name": product_name,
        "sku": product_sku,
        "price": product_price,
        "stock": product_stock,
        "link": product_link,
    }
    return product_sku, product_dict


def get_all_items_to_check(source):
    soup = BeautifulSoup(source, "lxml")

    main_content = soup.findAll(
        "li", {"class": "cs-product-gallery__item js-productad"}
    )
    if not main_content:
        raise ValueError("No main content found")
    return main_content


def check_changes(source, json_items_list_instance: JsonItemsHandler):
    """Check for changes on a website."""
    changed_or_new_items = []
    items_list = json_items_list_instance.read_json_file()

    for item in get_all_items_to_check(source):
        single_result_sku, single_result_dict = scrap_single_item(item)

        # ic(single_result_dict[single_result_sku])
        # ic(json_items_list[single_result_sku])

        if single_result_sku in items_list.keys():
            if single_result_dict[single_result_sku] != items_list[single_result_sku]:
                ic("Changes found")
                items_list[single_result_sku] = single_result_dict[single_result_sku]
                changed_or_new_items.append(single_result_dict[single_result_sku])
                json_items_list_instance.append_to_json_file(data=items_list)
        else:
            ic("New product added")
            changed_or_new_items.append(single_result_dict[single_result_sku])
            json_items_list_instance.append_to_json_file(data=single_result_dict)

    if changed_or_new_items:
        ic(changed_or_new_items)
        send_email(changed_or_new_items)


if __name__ == "__main__":
    request = RequestHandler()
    json_project_config = JsonHandler("projects_configs", "arttidesign.json")
    json_items_list = JsonItemsHandler("items_list_output", "arttidesign_items.json")
    # response = request.read_url("https://arttidesign.com.ua/ua/g86105736-vertikalnye-dizajnerskie-radiatory/")
    # check_changes(response.text, json_items_list)

    check_changes(read_html_file("test_container"), json_items_list)
    # send_email("test")

    # i = 1
    # while i < 3:
    #     paginator_url = read_json_file("arttidesign")["paginator_pattern"].replace(
    #         "$page", str(i)
    #     )
    #     page_request = request.read_url(paginator_url)
    #     ic("Processing", paginator_url, page_request.status_code)
    #
    #     if page_request.status_code != 200:
    #         break
    #
    #     new_data = scrap_single_product_data(page_request.text)
    #     append_to_json_file(new_data, "arttidesign")
    #     i += 1

    # paginator_links = request.read_url()
    # paginator_links = scrap.scrap_links(category.text, "b-pager__link", "https://arttidesign.com.ua")
    # ic(paginator_links)
    # ic(len(paginator_links))

    # request.read_url()
    # for i in params_file.read_json_file("arttidesign")["links"].values():
    #     request.read_url(i, delay=0.5)
