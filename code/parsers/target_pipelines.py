import fnmatch
import logging
from models.pipelines import Pipeline

from parsers.base_parser import BaseParser

logger = logging.getLogger("monorepo")

class TargetPipelineParser(BaseParser):
    def __init__(self, backend, req):
        try:
          self.target = req['build']['params']['target']
        except KeyError:
          self.target = None

        self.is_pipeline_parser = True

    def parse_pipeline(self, pipe: Pipeline) -> list[Pipeline]:
        if self.target is None or fnmatch.fnmatch(pipe.get_name(), f"*{ self.target }*"):
            return [pipe]
        else:
            return []