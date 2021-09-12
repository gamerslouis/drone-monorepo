from utils.utils import merge_dict
import json
import copy

class Step(json.JSONEncoder):
    def __init__(self, step):
        _step = copy.deepcopy(step)
        self.__name = _step.pop("name")
        self.__commands = _step.pop('commands', [])
        self.__settings = _step.pop('settings', {})
        self.__environment = _step.pop('environment', {})
        self.__image = _step.pop("image")
        self.__when = _step.pop('when', {})
        self.__others = _step

    def set_when(self, when):
        self.__when = when

    def get_when(self):
        return self.__when

    def set_name(self, name):
        self.__name = name

    def get_name(self):
        return self.__name

    def clone(self):
        return Step(merge_dict({}, self.to_json()))

    def to_json(self):
        return {
            'name': self.__name,
            'image': self.__image,
            'commands': self.__commands,
            'settings': self.__settings,
            'environment': self.__environment,
            'when': self.__when,
            **self.__others
        }

    def get_info(self, attr):
      if attr not in ['environment', 'name', 'metadata', 'steps']:
        raise Exception(f"cant access { attr }")
      return self.__dict__[f"_Step__{ attr }"]
