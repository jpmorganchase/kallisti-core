from abc import abstractmethod, ABC
from typing import Any


class Observer(ABC):
    """
    The Observer interface declares the update method, used by subjects.
    """

    @abstractmethod
    def update(self, **kwargs: Any):
        pass
