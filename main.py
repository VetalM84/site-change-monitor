"""Main file to scrap items."""

import json
import os
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
        __headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/111.0.0.0 Safari/537.36"
        }
        self._headers = __headers

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

    def read_json_file(self):
        """Read json file."""
        try:
            with open(self.full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except FileNotFoundError as e:
            ic(e)
            return {}


class JsonProjectConfig(JsonHandler):
    """Class to work with json files with project config."""

    def __init__(
        self, file_dir: str = "projects_configs", file_name: str = "new_project.json"
    ):
        super().__init__(file_dir, file_name)
        self._project_root = self.get_project_config()
        self.home_url = self._project_root["home_url"]
        self.paginator_pattern = self._project_root["paginator_pattern"]
        self.pagination_count = self._project_root["paginator_count"]
        self.items_container = self._project_root["items_container"]
        self._item_fields = self.get_project_config()["item_fields"]
        self.title = self._item_fields.get("title", None)
        self.sku = self._item_fields.get("sku", None)
        self.price = self._item_fields.get("price", None)
        self.stock = self._item_fields.get("stock", None)
        self.link = self._item_fields.get("link", None)

    def get_project_config(self) -> dict:
        """Get project config."""
        return self.read_json_file()


def find_all_project_files(file_dir) -> list:
    """Find all json project config files in a directory."""
    dir_path = Path(file_dir)
    files = os.listdir(dir_path)
    return [f for f in files if f.endswith(".json")]


class JsonItems(JsonHandler):
    """Class to work with json files with items."""

    def __init__(self, file_dir: str, file_name: str):
        super().__init__(file_dir, file_name)
        # Check if the directory exists, and create it if it doesn't.
        Path(file_dir).mkdir(parents=True, exist_ok=True)

    def read_json_file(self):
        """Read json items file, create it if it is not exists."""
        if not self.full_path.exists():
            with open(self.full_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
        with open(self.full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

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


# def scrap_links(source, project_settings: JsonProjectConfig) -> list:
#     """Scrap links."""
#     links = []
#     soup = BeautifulSoup(source, "lxml")
#
#     for link_tag in soup.findAll(
#         project_settings.items_container["tag"],
#         {"class": project_settings.items_container["class"]},
#     ):
#         links.append(project_settings.home_url + link_tag.get("href"))
#
#     return links


# def scrap_links(source, link_css_class: str, domain: str) -> list:
#     """Scrap links."""
#     links = []
#     soup = BeautifulSoup(source, "lxml")
#
#     for link_tag in soup.findAll("a", {"class": link_css_class}):
#         links.append(domain + link_tag.get("href"))
#
#     return links


def scrap_single_item(source, project_settings: JsonProjectConfig) -> Tuple[str, dict]:
    """Scrap product data for single product for arttidesign."""
    product_dict = {}

    product_name = source.find(
        project_settings.title["tag"], {"class": project_settings.title["class"]}
    ).text.strip()
    ic(product_name)
    product_link = source.find(
        project_settings.link["tag"], {"class": project_settings.link["class"]}
    ).get("href")
    ic(product_link)
    product_price = source.find(
        project_settings.price["tag"], {"class": project_settings.price["class"]}
    ).text.strip()
    ic(product_price)
    # TODO: fix replace in sku
    product_sku = (
        source.find(
            project_settings.sku["tag"], {"class": project_settings.sku["class"]}
        )
        .text.strip()
        .replace("Код: ", "")
    )
    ic(product_sku)
    product_stock = source.find(
        project_settings.stock["tag"], {"class": project_settings.stock["class"]}
    ).text.strip()
    ic(product_stock)

    product_dict[product_sku] = {
        "name": product_name,
        "sku": product_sku,
        "price": product_price,
        "stock": product_stock,
        "link": project_settings.home_url + product_link,
    }
    return product_sku, product_dict


def get_all_items_to_check(source, project_settings: JsonProjectConfig):
    """Load project and get all items to check."""
    soup = BeautifulSoup(source, "lxml")

    main_content = soup.findAll(
        project_settings.items_container["tag"],
        {"class": project_settings.items_container["class"]},
    )
    if not main_content:
        raise ValueError("No items in main content found")
    return main_content


def check_changes(
    source, items_list_instance: JsonItems, project_settings: JsonProjectConfig
) -> list[dict]:
    """Check for changes on a website."""
    changed_or_new_items: list[dict] = []
    items_list = items_list_instance.read_json_file()

    for item in get_all_items_to_check(source, project_settings):
        single_result_sku, single_result_dict = scrap_single_item(
            item, project_settings
        )

        # ic(single_result_dict[single_result_sku])
        # ic(json_items_list[single_result_sku])

        if single_result_sku in items_list.keys():
            if single_result_dict[single_result_sku] != items_list[single_result_sku]:
                ic("Changes found")
                items_list[single_result_sku] = single_result_dict[single_result_sku]
                changed_or_new_items.append(single_result_dict[single_result_sku])
                items_list_instance.append_to_json_file(data=items_list)
        else:
            ic("New product added")
            changed_or_new_items.append(single_result_dict[single_result_sku])
            items_list_instance.append_to_json_file(data=single_result_dict)

    return changed_or_new_items


def main():
    """Main function to start the process for every project and send an email if there is any."""
    changed_or_new_items: list[dict] = []
    request = RequestHandler()

    for project in find_all_project_files("projects_configs"):
        json_project_config = JsonProjectConfig(
            file_dir="projects_configs", file_name=project
        )
        json_items_list = JsonItems(
            file_dir="items_list_output", file_name="output_" + project
        )

        # iterate over pagination
        for page_index in range(1, json_project_config.pagination_count + 1):
            paginator_url = json_project_config.paginator_pattern.replace(
                "$page", str(page_index)
            )
            response = request.read_url(url=paginator_url)
            ic("Processing", paginator_url, response.status_code)

            if response.status_code != 200:
                break
            changed_or_new_items.extend(
                check_changes(
                    source=response.text,
                    items_list_instance=json_items_list,
                    project_settings=json_project_config,
                )
            )
            # check_changes(
            #     read_html_file("test_container"), json_items_list, json_project_config
            # )
            # ic(changed_or_new_items)
        if changed_or_new_items:
            ic(changed_or_new_items)
            send_email(changed_or_new_items)


# async def run_task_every_x_seconds(x):
#     # Schedule the task to run every x seconds
#     aioschedule.every(x).seconds.do(my_task)
#     while True:
#         await aioschedule.run_pending()
#         await asyncio.sleep(1)
#
# async def main():
#     # Run the task every 5 seconds
#     await run_task_every_x_seconds(5)
#
# # Run the main function in an event loop
# asyncio.run(main())


if __name__ == "__main__":

    main()
