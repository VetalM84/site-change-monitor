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
        self.__headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/111.0.0.0 Safari/537.36"
        }

    def set_headers(self, headers: dict) -> None:
        """Set headers."""
        self.__headers = headers

    def read_url(self, url: str, delay: int = 0) -> Response:
        """Read url and return response. Delay is in seconds."""
        response = requests.get(url, headers=self.__headers)
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
        self.modules = self._project_root["modules"]

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


def scrap_single_item(source, project_settings: dict) -> Tuple[str, dict]:
    """Scrap product data for single product."""

    product_dict_sku, product_dict = {}, {}
    item_fields = project_settings["item_fields"]

    # iterate over all fields in item_fields
    for field in item_fields:
        # find a container with the fields
        result = source.find(
            item_fields[field].get("tag"), class_=item_fields[field].get("class")
        )
        # scrap data from the container
        try:
            if item_fields[field].get("text"):
                result = result.text
            if item_fields[field].get("strip"):
                result = result.strip()
            if item_fields[field].get("attr"):
                result = result.get(item_fields[field].get("attr"))
            if item_fields[field].get("prepend"):
                result = item_fields[field].get("prepend") + result
        except (KeyError, AttributeError) as e:
            ic(e)
            pass

        if result:
            product_dict[field] = result

    product_dict_sku[product_dict["sku"]] = product_dict
    return product_dict["sku"], product_dict_sku


def get_all_items_to_check(
    source, project_settings: JsonProjectConfig, module_index: int = 0
) -> list:
    """Load project and get a container with all items to check. Returns a list of items."""
    soup = BeautifulSoup(source, "lxml")

    items_container = project_settings.modules[module_index].get("items_container")
    single_item_container = project_settings.modules[module_index].get(
        "single_item_container"
    )

    # check if there is a container with all items
    if items_container:
        # search for a container by tag and class or by selector
        if items_container.get("tag"):
            items_container = soup.find(
                items_container["tag"], class_=items_container["class"]
            )
        else:
            items_container = soup.select_one(items_container.get("selector"))

        # extract all items from the container to list
        all_items_list = items_container.findAll(
            single_item_container["tag"], class_=single_item_container["class"]
        )
    else:
        # search for a single item
        all_items_list = soup.findAll(
            single_item_container["tag"], class_=single_item_container["class"],
            limit=1
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
    module_index: int = 0,
) -> list[dict]:
    """Check for changes on a website."""
    changed_or_new_items: list[dict] = []
    # load existing items list from the json file
    items_list = items_list_instance.read_json_file()

    # iterate over all items in the list
    for item in get_all_items_to_check(source, project_settings, module_index):
        single_result_sku, single_result_dict = scrap_single_item(
            item, project_settings.modules[module_index]
        )

        # check if the item is in the list
        if single_result_sku in items_list.keys():
            # check if the item has changed
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


def main(request_delay: int = 0, headers: dict = None) -> None:
    """Main function to start the process for every project and send an email if there is any."""
    request = RequestHandler()
    # set custom headers if any
    if headers:
        request.set_headers(headers=headers)

    # iterate over all projects
    for project in JsonProjectConfig.find_all_project_files():
        changed_or_new_items: list[dict] = []
        # instantiate project config class
        json_project_config = JsonProjectConfig(file_name=project)
        # instantiate storage class depend on the hosting
        if USE_AWS_S3_STORAGE:
            json_items_list = JsonItemsS3Storage(file_name="output_" + project)
        else:
            json_items_list = JsonItemsLocalStorage(file_name="output_" + project)

        # iterate over all modules in the project
        for index, module in enumerate(json_project_config.modules, start=0):

            # if there is a paginator pattern, iterate over all pages
            if module.get("paginator_pattern"):
                # iterate over pagination
                for page_index in range(1, module.get("paginator_count", 0) + 1):
                    paginator_url = module.get("paginator_pattern").replace(
                        "$page", str(page_index)
                    )
                    response = request.read_url(url=paginator_url, delay=request_delay)
                    ic(paginator_url, response.status_code)

                    if response.status_code != 200:
                        break
            else:
                # if there is no paginator, just load the single url
                response = request.read_url(
                    url=module.get("single_url"), delay=request_delay
                )
                ic(module.get("single_url"), response.status_code)

            # add new items to the dict
            changed_or_new_items.extend(
                check_changes(
                    source=response.text,
                    items_list_instance=json_items_list,
                    project_settings=json_project_config,
                    module_index=index,
                )
            )

        # send email if there are any changes
        if changed_or_new_items:
            send_email(
                f"Changes detected in {json_project_config.project_name}",
                changed_or_new_items,
            )


def schedule_task(hours_interval: int, request_delay: int = 0, headers: dict = None):
    # Run the task once immediately
    main(request_delay=request_delay, headers=headers)
    # Schedule the task to run every x hours
    schedule.every(hours_interval).hours.do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    schedule_task(hours_interval=24, request_delay=3)
