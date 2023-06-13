# -*- coding:utf-8 -*-
# author: kusen
# email: 1194542196@qq.com
# date: 2023/4/13


import itertools
from collections.abc import MutableMapping

from .fields import Filed, CheckField


class ItemMeta(object):
    def __new__(cls, *args, **kwargs):
        fields = {}
        for n in dir(cls):
            v = getattr(cls, n)
            if isinstance(v, Filed):
                fields[n] = v
        cls.fields = fields
        return super().__new__(cls)


class CheckItem(MutableMapping, ItemMeta):
    relate_process_default = []  # 关联处理字段间互相取默认值
    relate_check_null = []  # 关联检查字段间互相是否为None
    relate_check_sequence_length = []  # 关联检查序列字段间互相长度判断
    relate_check_startswith = []  # 关联检查字符串字段间互相startswith关系
    relate_check_endswith = []  # 关联检查字符串字段间互相endswith关系
    relate_check_contains = []  # 关联检查字符串字段间互相包含关系
    bundle_errors = []  # 是否一次性返回所有错误，暂时没有使用该字段

    def __init__(self, *args, **kwargs):
        self._values = {}
        self._base_values = {}
        if args or kwargs:
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def process(self):
        for key in itertools.chain(self._get_config_attr_names(),
                                   self.fields.keys()):
            field_name = key
            if not key.startswith('_'):
                field_name = '_' + field_name
            process_method_name = '_process' + field_name
            if not hasattr(self, process_method_name):
                continue
            getattr(self, process_method_name)()

    def check(self):
        for key in itertools.chain(self._get_config_attr_names(),
                                   self.fields.keys()):
            field_name = key
            if not key.startswith('_'):
                field_name = '_' + field_name
            check_method_name = '_check' + field_name
            if not hasattr(self, check_method_name):
                continue
            getattr(self, check_method_name)()

    def _process_relate_process_default(self):
        for field1, field2 in self.relate_process_default:
            if self[field1] is None and self[field2] is not None:
                self[field1] = self[field2]

    def _check_relate_check_contains(self):
        for field1, field2 in self.relate_check_contains:
            value1, value2 = self[field1], self[field2]
            if value1 is None or value2 is None:
                return
            if value2 not in value1:
                raise Exception('Field %s must be contain field %s' % (
                    field1, field2
                ))

    def _check_relate_check_endswith(self):
        for field1, field2 in self.relate_check_endswith:
            value1, value2 = self[field1], self[field2]
            if value1 is None or value2 is None:
                return
            if not value1.endswith(value2):
                raise Exception('Field %s must be endswith field %s' % (
                    field1, field2
                ))

    def _check_relate_check_startswith(self):
        for field1, field2 in self.relate_check_startswith:
            value1, value2 = self[field1], self[field2]
            if value1 is None or value2 is None:
                return
            if not value1.startswith(value2):
                raise Exception('Field %s must be startswith field %s' % (
                    field1, field2
                ))

    def _check_relate_check_null(self):
        for field1, field2 in self.relate_check_null:
            if self[field2] is not None and self[field1] is None:
                raise Exception(("Field %s is not null, so field %s "
                                 "also is not null") % (field2, field1))

    def _check_relate_check_sequence_length(self):
        for field1, field2 in self.relate_check_sequence_length:
            value1, value2 = self[field1], self[field2]
            if not isinstance(value1, (list, tuple)) or not isinstance(
                    value2, (list, tuple)
            ):
                raise Exception('Field %s and %s all must be sequence type' % (
                    field1, field2
                ))
            if len(value1) != len(value2):
                raise Exception(
                    'Field %s and %s sequence length is different' % (
                        field1, field2
                    ))

    def _get_config_attr_names(self):
        attr_names = []
        for k in dir(self.__class__):
            if k.startswith('relate_process_') or k.startswith(
                    'relate_check_') or k == 'bundle_errors':
                attr_names.append(k)
        return attr_names

    def __setitem__(self, key, value):
        self._base_values[key] = value
        if key in self.fields:
            if isinstance(self.fields[key], CheckField):
                fe = self.fields[key].from_instance()
                fe.input(key, value)
                self._values[key] = fe.value
            else:
                self._values[key] = value
        else:
            raise KeyError(
                f"{self.__class__.__name__} does not support field: {key}")

    def __getitem__(self, key):
        if key in self._values:
            return self._values[key]
        elif key in self.fields:
            self[key] = None
            return self[key]
        elif key in self.__dict__:
            return self.__dict__[key]
        else:
            raise KeyError(
                f"{self.__class__.__name__} does not have field: {key}")

    def __delitem__(self, key):
        del self._values[key]

    def __len__(self):
        return len(self.__dict__.keys())

    def __iter__(self):
        self._process_and_check()
        return iter(self.fields)

    def _process_and_check(self):
        self.process()
        self.check()

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        raise AttributeError(f"Use item[{name!r}] to get field value")

    def __setattr__(self, name, value):
        if name in self.__dict__ or name in ['_values', '_base_values']:
            self.__dict__[name] = value
        else:
            raise AttributeError(
                f"Use item[{name!r}] = {value!r} to set field value")

    def keys(self):  # to dict时优先调用，不会调用__iter__和__len__，但必须实现
        self._process_and_check()
        keys = self.fields.keys()
        _ = [self[field] for field in keys]  # 补全所有字段数据
        return keys

    def get_base_value(self, key):
        if key in self._base_values:
            return self._base_values[key]
        else:
            raise KeyError(
                f"{self.__class__.__name__} does not support field: {key}")
