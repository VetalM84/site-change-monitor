"""Main module contains a class to work with files and file path."""

import json
from pathlib import Path

from icecream import ic


class JsonHandler:
    """Class to work with json files."""

    _file_dir: str = None

    def __init__(self, file_name: str):
        self._file_name = file_name
        self.full_path = self.set_full_path()

    def set_full_path(self) -> Path:
        """Set ful path file dir."""
        folder_path = Path(self._file_dir)
        file_path = Path(self._file_name)
        return folder_path / file_path

    def read_json_file(self):
        """Read json file and return empty dictionary if it is not exists."""
        try:
            with open(self.full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except FileNotFoundError as e:
            ic(e)
            return {}
