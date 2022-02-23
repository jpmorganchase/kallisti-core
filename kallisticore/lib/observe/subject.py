import logging
from abc import ABC
from typing import List, Any

from kallisticore.lib.observe.observer import Observer


class Subject(ABC):
    logger = logging.getLogger(__name__)

    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        self.logger.info("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        self._observers.remove(observer)

    def notify(self, **kwargs: Any) -> None:
        """
        Notify all observers about an event.
        """
        self.logger.info("Subject: Notifying observers...")
        for observer in self._observers:
            try:
                observer.update(**kwargs)
            except Exception as e:
                self.logger.error(str(e))
