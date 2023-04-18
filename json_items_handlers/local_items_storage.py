"""Module to work with json items files on local storage."""

import json
from pathlib import Path

from json_items_handlers.json_handler import JsonHandler


class JsonItemsLocalStorage(JsonHandler):
    """Class to work with json files contains items on local storage."""

    _file_dir: str = "items_list_output"

    def __init__(self, file_name: str):
        super().__init__(file_name)
        # Check if the directory exists, and create it if it doesn't.
        Path(self._file_dir).mkdir(parents=True, exist_ok=True)

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
