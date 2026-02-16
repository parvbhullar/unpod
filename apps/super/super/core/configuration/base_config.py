# import logging
from abc import abstractmethod, ABC
# from pathlib import Path
# import inflection


class BaseModelConfig(ABC):
    @abstractmethod
    def get_config(self, token, **kwargs):
        pass

    # @abstractmethod
    # def send_config(self, token, **kwargs):
    #     pass