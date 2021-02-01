from utils.utils import merge_dict
import json

class Step(json.JSONEncoder):
    def __init__(self, step):
        self.__name = step["name"]
        self.__commands = step['commands'] if 'commands' in step else []
        self.__settings = step['settings'] if 'settings' in step else {}
        self.__environment = step['environment'] if 'environment' in step else {}
        self.__image = step['image']
        self.__when = step["when"] if "when" in step else {}

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
            'when': self.__when
        }

    def get_info(self, attr):
      if attr not in ['environment', 'name', 'metadata', 'steps']:
        raise Exception(f"cant access { attr }")
      return self.__dict__[f"_Step__{ attr }"]
