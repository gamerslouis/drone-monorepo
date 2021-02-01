import logging
import json
import yaml

from models.steps import Step
from utils.utils import merge_dict

logger = logging.getLogger('monorepo')

class Pipeline(json.JSONEncoder):
    def __init__(self, pipe: dict):
      self.__raw = pipe
      self.platform = pipe['platform'] if 'platform' in pipe else {}
      self.__type = pipe['type']
      self.__kind = 'pipeline'
      self.__trigger = pipe['trigger'] if 'trigger' in pipe else {}

      if 'steps' in pipe:
          self.__steps = [ Step(step) if not isinstance(step, Step) else step for step in pipe['steps'] ]
      else:
          self.__steps = []


    def merge_pipeline(self, target):
        merged_pipeline = self.__raw.copy()

        for k, v in target.items():
            if k in merged_pipeline:
                if isinstance(v, str):
                    merged_pipeline[k] = v
                elif isinstance(v, list):
                    merged_pipeline[k] = merged_pipeline[k] + v
                elif isinstance(v, dict):
                    merged_pipeline[k] = merge_dict(merged_pipeline[k], v)
            else:
                merged_pipeline[k] = v

        return merged_pipeline

    def set_steps(self, steps):
        self.__steps = steps
        self.__raw['steps'] = steps

    def get_steps(self):
        return self.__steps

    def get_trigger(self):
        return self.__trigger

    def set_trigger(self, trigger):
        self.__trigger = trigger
        self.__raw['trigger'] = trigger

    def get_kind(self):
        return self.__kind

    def get_type(self):
        return self.__type

    def clone(self):
        return Pipeline(merge_dict({}, self.__raw))

    def get_raw(self):
        return self.__raw.copy()

    def to_text(self):
        raw = self.__raw.copy()
        raw['steps'] = [ s.to_json() for s in self.__raw['steps'] ]

        return yaml.safe_dump(raw)

    def to_json(self):
        raw = self.__raw.copy()
        raw['steps'] = [ json.dumps(s) for s in self.__raw['steps'] ]

        return raw
