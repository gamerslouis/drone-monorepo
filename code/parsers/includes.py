import logging

from models.pipelines import Pipeline
from parsers.base_parser import BaseParser

logger = logging.getLogger('mono')

class IncludesParser(BaseParser):
    def __init__(self, backend, req = None):
        self.backend = backend
        self.repo = req["repo"]["slug"]
        self.commit = req["build"]["after"]

        self.is_pipeline_parser = True        

    def parse_pipeline(self, pipe: Pipeline) -> list[Pipeline]:
        return_pipelines = [pipe]

        inc = pipe.get_pipeline_include()
        if inc is not None:
            included = self.backend.get_included_pipeline(inc, self.repo, self.commit)

            if included != "":
                return_pipelines = [pipe.merge_pipeline(included)]

        return return_pipelines