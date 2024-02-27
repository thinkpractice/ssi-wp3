from typing import List
import os


class AnalysisDirectories:
    def __init__(self, base_directory: str):
        self.__base_directory = base_directory

    @property
    def base_directory(self) -> str:
        return self.__base_directory

    @property
    def directories(self) -> List[str]:
        return [
            os.path.join(self.base_directory, "plots"),
            os.path.join(self.base_directory, "wordclouds"),
            os.path.join(self.base_directory, "data")
        ]