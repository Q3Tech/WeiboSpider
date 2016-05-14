# -*- coding: utf-8 -*-
"""提供类的序列化和反序列化工具."""
import json
from json import JSONEncoder


class JsonSerializable(object):
    """可序列化的"""
    def to_json_dict(self):
        raise NotImplementedError

    @classmethod
    def from_json_dict(cls):
        raise NotImplementedError


class JsonSerializableEncoder(JSONEncoder):
    """当类继承JsonSerializable时,使用该类序列化."""
    def default(self, obj):
        if isinstance(obj, JsonSerializable):
            return obj.to_json_dict()
        return json.JSONEncoder.default(self, obj)
