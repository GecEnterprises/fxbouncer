from typing import List, Tuple

class Downloadable:
    def __init__(self, title: str, possible_urls: List[str]):
        self.title = title
        self.possible_urls = possible_urls