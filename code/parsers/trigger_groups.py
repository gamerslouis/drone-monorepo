from models.pipelines import Pipeline
from models.steps import Step

from parsers.base_parser import BaseParser

import logging

logger = logging.getLogger("monorepo")

class TriggerGroupsParser(BaseParser):
    def __init__(self, backend = None, req = None):
        self.is_pipeline_parser = True
        self.is_step_parser = True

    def parse_pipeline(self, pipe: Pipeline) -> list[Pipeline]:
        triggers = pipe.get_trigger()

        if not isinstance(triggers, list):
            return [pipe]

        return_pipelines = []
        for index, t in enumerate(triggers):
            newPipe = pipe.clone()
            newPipe.set_trigger(t)
            newPipe.set_name(f"{ index+1 }-{ pipe.get_name() }")
            return_pipelines.append(newPipe)

        return return_pipelines


    def parse_step(self, step: Step) -> list[Step]:
        when = step.get_when()
        if not isinstance(when, list):
            return [step]

        steps = []
        for index, cond in enumerate(when):
            modified_step = step.clone()
            modified_step.set_name(f"{ index+1 }-{ step.get_name() }")
            modified_step.set_when(cond)

            steps.append(modified_step)
          
        return steps