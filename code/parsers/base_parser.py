import abc
from models.pipelines import Pipeline
from models.steps import Step

class BaseParser:
    is_pipeline_parser = False
    is_step_parser = False

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, backend, req):
      pass

    @abc.abstractmethod
    def parse_pipeline(self, pipe: Pipeline) -> list[Pipeline]:
      raise NotImplementedError("Please implement this method")

    @abc.abstractmethod
    def parse_step(self, step: Step) -> list[Step]:
      raise NotImplementedError("Please implement this method")