from utils.utils import merge_dict, ComplexEncoder
import json
import yaml

class Step(json.JSONEncoder):
    def __init__(self, step):
        self.__raw = step.copy()
        self.__name = step["name"]

        self.__when = step["when"] if "when" in step else {}

    def set_when(self, when):
        self.__raw['when'] = when
        self.__when = when

    def get_when(self):
        return self.__when

    def set_name(self, name):
        self.__raw['name'] = name
        self.__name = name

    def get_name(self):
        return self.__name

    def clone(self):
        return merge_dict({}, self.__raw.copy())

    def to_json(self):
        return self.__raw
