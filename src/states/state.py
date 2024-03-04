from abc import ABC, abstractmethod
from pygame.surface import Surface
from pygame.event import Event

class State(ABC):
    @abstractmethod
    def draw(self, screen: Surface):
        pass

    @abstractmethod
    def update(self, delta: int):
        pass

    @abstractmethod
    def handle_event(self, event: Event):
        pass