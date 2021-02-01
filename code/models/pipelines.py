import logging
import json
import yaml

from models.steps import Step
from utils.utils import merge_dict

logger = logging.getLogger('monorepo')

class Pipeline(json.JSONEncoder):
    def __init__(self, pipe: dict):
      self.__platform = pipe['platform'] if 'platform' in pipe else {}
      self.__type = pipe['type'] if 'type' in pipe else None
      self.__environment = pipe['environment'] if 'environment' in pipe else {}
      self.__trigger = pipe['trigger'] if 'trigger' in pipe else {}
      self.__name = pipe['name']
      self.__include_pipeline = pipe['include_pipeline'] if 'include_pipeline' in pipe else None
      self.__metadata = pipe['metadata'] if 'metadata' in pipe else {}

      if 'steps' in pipe:
          self.__steps = [ Step(step) if not isinstance(step, Step) else step for step in pipe['steps'] ]
      else:
          self.__steps = []

    def merge_pipeline(self, target):
        merged_pipeline = self.to_json().copy()

        # logger.debug("Base:")
        # logger.debug(self.to_json())
        # logger.debug("Target:")
        # logger.debug(target)
        for k, v in target.items():
            if k in merged_pipeline:
                if isinstance(v, list):
                    merged_pipeline[k] = merged_pipeline[k] + v
                elif isinstance(v, dict):
                    merged_pipeline[k] = merge_dict(merged_pipeline[k], v)
                else:
                    merged_pipeline[k] = v
            else:
                merged_pipeline[k] = v

        # logger.debug("Returned: ")
        # logger.debug(merged_pipeline)
        return Pipeline(merged_pipeline)

    def set_steps(self, steps: list[Step]) -> None:
        self.__steps = steps

    def get_steps(self) -> list[Step]:
        return self.__steps

    def get_trigger(self):
        return self.__trigger

    def set_trigger(self, trigger) -> None:
        self.__trigger = trigger

    def get_type(self) -> str:
        return self.__type

    def get_name(self) -> str:
        return self.__name

    def set_name(self, name) -> str:
        self.__name = name

    def clone(self):
        return Pipeline(merge_dict({}, self.to_json()))

    def get_pipeline_include(self):
        return self.__include_pipeline

    def to_json(self) -> dict:
        return {
          'name': self.__name,
          'kind': 'pipeline',
          'type': self.__type,
          'trigger': self.__trigger,
          'environment': self.__environment,
          'platform': self.__platform,
          'steps': [ s.to_json() for s in self.__steps ],
          'metadata': self.__metadata
        }

    def get_info(self, attr):
      if attr not in ['environment', 'name', 'metadata', 'steps']:
        raise Exception(f"cant access { attr }")
      return self.__dict__[f"_Pipeline__{ attr }"]