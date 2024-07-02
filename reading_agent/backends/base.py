from abc import ABC
from typing import Tuple


class BackendBase(ABC):
    def query_model(self, prompt: str) -> Tuple[int, str]:
        """

        Args:
            prompt (str):

        Returns:
            int: token usage
            str: response
        """
        raise NotImplementedError
