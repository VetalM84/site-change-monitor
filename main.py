"""Main file to scrap items."""

import logging
import os
import time
from pathlib import Path
from typing import Tuple, Union

import requests
import schedule
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from icecream import ic
from requests import Response

from json_items_handlers import JsonHandler, JsonItemsLocalStorage, JsonItemsS3Storage
from mail import send_email

load_dotenv()

USE_AWS_S3_STORAGE = bool(int(os.getenv("USE_AWS_S3_STORAGE")))

logging.basicConfig(
    filename="run.log",
    datefmt="%d-%m-%Y %H:%M:%S",
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s:%(message)s",
)


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


class JsonProjectConfig(JsonHandler):
    """Class to work with json files with project config."""

    _file_dir: str = "projects_configs"

    def __init__(self, file_name: str):
        super().__init__(file_name)
        self._project_root = self.get_project_config()
        self.project_name = self._project_root["project_name"]
        self.home_url = self._project_root["home_url"]
        self.paginator_pattern = self._project_root["paginator_pattern"]
        self.pagination_count = self._project_root["paginator_count"]
        self.items_container = self._project_root["items_container"]
        self.single_item_container = self._project_root["single_item_container"]
        self.item_fields = self.get_project_config()["item_fields"]
        if "sku" not in self.item_fields:
            logging.error(f"sku field not found in item_fields for {self.project_name}")
            ic("sku field not found")

    def get_project_config(self) -> dict:
        """Get project config."""
        if not Path(self._file_dir).exists():
            Path(self._file_dir).mkdir(parents=True, exist_ok=True)
        return self.read_json_file()

    @staticmethod
    def find_all_project_files(file_dir: str = _file_dir) -> list:
        """Find all json project config files in a directory."""
        dir_path = Path(file_dir)
        files = os.listdir(dir_path)
        return sorted([f for f in files if f.endswith(".json")])


def scrap_single_item(source, project_settings: JsonProjectConfig) -> Tuple[str, dict]:
    """Scrap product data for single product."""

    product_dict_sku, product_dict = {}, {}

    for field in project_settings.item_fields:
        result = source.find(
            project_settings.item_fields[field].get("tag"),
            class_=project_settings.item_fields[field].get("class"),
        )
        try:
            if project_settings.item_fields[field].get("text"):
                result = result.text
            if project_settings.item_fields[field].get("strip"):
                result = result.strip()
            if project_settings.item_fields[field].get("attr"):
                result = result.get(project_settings.item_fields[field].get("attr"))
            if project_settings.item_fields[field].get("prepend"):
                result = project_settings.item_fields[field].get("prepend") + result
        except (KeyError, AttributeError) as e:
            ic(e)
            pass

        if result:
            product_dict[field] = result

    product_dict_sku[product_dict["sku"]] = product_dict
    return product_dict["sku"], product_dict_sku


def get_all_items_to_check(source, project_settings: JsonProjectConfig) -> list:
    """Load project and get all items to check."""
    soup = BeautifulSoup(source, "lxml")
    if project_settings.items_container.get("tag"):
        items_container = soup.find(
            project_settings.items_container["tag"],
            class_=project_settings.items_container["class"],
        )
    else:
        items_container = soup.select_one(
            project_settings.items_container.get("selector")
        )

    all_items_list = items_container.findAll(
        project_settings.single_item_container["tag"],
        class_=project_settings.single_item_container["class"],
    )
    if not all_items_list:
        logging.error("No items in main content found")
        ic("No items in main content found")
        send_email(subject=f"No items in {project_settings.project_name} found")
    return all_items_list


def check_changes(
    source,
    items_list_instance: Union[JsonItemsLocalStorage, JsonItemsS3Storage],
    project_settings: JsonProjectConfig,
) -> list[dict]:
    """Check for changes on a website."""
    changed_or_new_items: list[dict] = []
    # load items list from json file
    items_list = items_list_instance.read_json_file()

    for item in get_all_items_to_check(source, project_settings):
        single_result_sku, single_result_dict = scrap_single_item(
            item, project_settings
        )

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
    request = RequestHandler()

    for project in JsonProjectConfig.find_all_project_files():
        changed_or_new_items: list[dict] = []
        json_project_config = JsonProjectConfig(file_name=project)
        # instantiate storage class depend on the hosting
        if USE_AWS_S3_STORAGE:
            json_items_list = JsonItemsS3Storage(file_name="output_" + project)
        else:
            json_items_list = JsonItemsLocalStorage(file_name="output_" + project)

        # iterate over pagination
        for page_index in range(1, json_project_config.pagination_count + 1):
            paginator_url = json_project_config.paginator_pattern.replace(
                "$page", str(page_index)
            )
            response = request.read_url(url=paginator_url, delay=3)
            ic(paginator_url, response.status_code)

            if response.status_code != 200:
                break

            changed_or_new_items.extend(
                check_changes(
                    source=response.text,
                    items_list_instance=json_items_list,
                    project_settings=json_project_config,
                )
            )

        if changed_or_new_items:
            # ic(changed_or_new_items)
            send_email(
                f"Changes detected in {json_project_config.project_name}",
                changed_or_new_items,
            )


def schedule_task(hours: int):
    # Schedule the task to run every x hours
    # TODO: change seconds to hours
    schedule.every(hours).seconds.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    # schedule_task(20)
    main()
