"""Main file to """

import time
from typing import Tuple

from icecream import ic
from mail import send_email
import requests
from bs4 import BeautifulSoup
import json

from requests import Response


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


def save_html_file(file_name, response, counter=0) -> None:
    """Save html file."""
    with open(f"data/{file_name}_{counter}.html", "w", encoding="utf-8") as f:
        f.write(response.text)


def read_html_file(file_name: str) -> str:
    """Read html file."""
    with open(f"data/{file_name}.html", "r", encoding="utf-8") as f:
        src = f.read()
    return src


def read_json_file(file_name: str) -> dict:
    """Read json file."""
    with open(f"json/{file_name}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_to_json_file(data, file_name: str) -> None:
    """Save data to json file."""
    with open(f"json/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def append_to_json_file(data, file_name: str) -> None:
    """Append data to json file."""
    existing_data = read_json_file(file_name)
    existing_data["items"].update(data)
    with open(f"json/{file_name}.json", "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)


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


def all_items_container(source):
    soup = BeautifulSoup(source, "lxml")

    main_content = soup.findAll(
        "li", {"class": "cs-product-gallery__item js-productad"}
    )
    return main_content


def check_changes(source):
    """Check for changes on a website."""
    changed_or_new_items = []
    json_items_list = read_json_file("arttidesign")["items"]

    for item in all_items_container(source):
        single_result_sku, single_result_dict = scrap_single_item(item)

        # ic(single_result_dict[single_result_sku])
        # ic(json_items_list[single_result_sku])

        if single_result_sku in json_items_list.keys():
            if (
                single_result_dict[single_result_sku]
                != json_items_list[single_result_sku]
            ):
                ic("Changes found")
                json_items_list[single_result_sku] = single_result_dict[
                    single_result_sku
                ]
                changed_or_new_items.append(single_result_dict[single_result_sku])
                append_to_json_file(json_items_list, "arttidesign")
        else:
            ic("New product added")
            changed_or_new_items.append(single_result_dict[single_result_sku])
            append_to_json_file(single_result_dict, "arttidesign")

    if changed_or_new_items:
        ic(changed_or_new_items)
        send_email(changed_or_new_items)


if __name__ == "__main__":

    # scrap product data
    request = RequestHandler()
    # response = request.read_url("https://arttidesign.com.ua/ua/g86105736-vertikalnye-dizajnerskie-radiatory/")
    # monitor_changes(response.text)

    check_changes(read_html_file("test_container"))
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

    # products = []
    # for i in range(0, 5):
    #     try:
    #         file = read_html_file(f"product_{i}")
    #         products.append(scrap_product_data(file))
    #         ic(f"Processing file {i}")
    #     except FileNotFoundError:
    #         ic(f"File {i} not found")
    #         break
    #
    # save_to_json(products, "items")
