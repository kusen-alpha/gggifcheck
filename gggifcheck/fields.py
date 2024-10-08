# -*- coding:utf-8 -*-
# author: kusen
# email: 1194542196@qq.com
# date: 2023/4/13
import copy
import re
import sys
import datetime


class Filed(object):
    """
    普通Field，不进行检查
    """
    pass


class CheckField(Filed):
    def __init__(self, key=None, value=None, default=None,
                 nullable=True, choices=None, types=None):
        """

        :param default: 默认值
        :param nullable: 是否能为None
        :param choices: 必须为其中一个
        :param types: 数据可支持的类型列表
        """
        self.key = key
        self._value = value
        self.default = default
        self.nullable = nullable
        self.choices = choices or []
        types = types or tuple()
        if not isinstance(types, (tuple, list)):
            types = (types,)
        self.types = types
        self._check_args()  # 检查初始参数合法性
        self._type_checked = True  # 类型是否检查
        self._input_checked = False  # input方法对_value进行检查与否

    def from_instance(self):
        """
        使用场景：开始创建一个实例模板，后续通过该模板进行多次独立进行检查
        :return:
        """
        new = copy.deepcopy(self)
        new.key = None
        new._value = None
        new._type_checked = True
        new._input_checked = False
        return new

    def input(self, key, value=None):
        self.key = key
        self._value = value
        self.check()
        self._input_checked = True

    def output(self):
        if not self._input_checked:
            self.check()
        if self._value is not None:
            return self.format(self._value)
        self._value = self.default
        self.check()
        return self.format(self._value)

    def format(self, value):
        return value

    @property
    def value(self):
        return self.output()

    @property
    def base_value(self):
        return self._value

    def check(self):
        errors = self._check()
        for error in errors:
            raise Exception(error)

    def _check(self):
        return [
            *self._check_types(),
            *self._check_nullable(),
            *self._check_choices(),
        ]

    def _check_types(self):
        if self._value is None or not self.types:
            return []
        if not isinstance(self._value, self.types):
            self._type_checked = False
            error_msg = ('Field %s input: %s, the type is %s, is not '
                         'types: %s') % (
                            self.key, self._value, type(self._value),
                            self.types)
            return [Exception(error_msg)]
        return []

    def _check_choices(self):
        if self.choices and self._value not in self.choices:
            error_msg = 'Field %s intput: %s, is not in choices: %s' % (
                self.key, self._value, self.choices)
            return [
                Exception(error_msg)
            ]
        return []

    def _check_args(self):
        if self.types and self.choices:
            for choice in self.choices:
                if isinstance(choice, self.types):
                    continue
                error_msg = ('The choices values correspond to types, '
                             'types: %s' % self.types)
                raise Exception(error_msg)

    def _check_nullable(self):
        if self._value is None and not self.nullable and not self.default:
            error_msg = 'Field %s intput: %s, but is not None' % (
                self.key, self._value)
            return [Exception(error_msg)]
        else:
            return []


class StringCheckField(CheckField):
    def __init__(self, min_length=None, max_length=None, contains=None,
                 excludes=None, *args, **kwargs):
        self.min_length = min_length if min_length is not None else -sys.maxsize
        self.max_length = max_length if max_length is not None else sys.maxsize
        self.contains = contains or []
        self.excludes = excludes or []
        super(StringCheckField, self).__init__(types=(str,), *args, **kwargs)

    def _check(self):
        return [
            *super(StringCheckField, self)._check(),
            *self._check_length(),
            *self._check_contains()
        ]

    def _check_args(self):
        super(StringCheckField, self)._check_args()
        if not isinstance(self.max_length, int) or not isinstance(
                self.min_length, int
        ):
            error_msg = ('The max_length and min_length must be'
                         'types: int')
            raise Exception(error_msg)

    def _check_length(self):
        if self._value is None or not isinstance(self._value, self.types):
            return []
        value_length = len(self._value)
        if value_length < self.min_length or value_length > self.max_length:
            error_msg = ('Field %s intput: %s, the value length is: %s,'
                         ' but the value length is (%s, %s)' % (
                             self.key, self._value, len(self._value),
                             self.min_length, self.max_length))
            return [Exception(error_msg)]
        return []

    def _check_contains(self):
        if self._value is None:
            return []
        for contain in self.contains:
            if not re.search(contain, self._value):
                error_msg = ('Field %s intput: %s, must contain '
                             'matching rules：%s' % (
                                 self.key, self._value, contain))
                return [Exception(error_msg)]
        for exclude in self.excludes:
            if re.search(exclude, self._value):
                error_msg = 'Field %s intput: %s, can not contain：%s' % (
                    self.key, self._value, exclude)
                return [Exception(error_msg)]
        return []


class IntegerCheckField(CheckField):
    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        self.min_value = min_value if min_value is not None else -sys.maxsize
        self.max_value = max_value if max_value is not None else sys.maxsize
        super(IntegerCheckField, self).__init__(types=(int,), *args, **kwargs)

    def _check(self):
        return [
            *super(IntegerCheckField, self)._check(),
            *self._check_value_between(),
        ]

    def _check_args(self):
        super(IntegerCheckField, self)._check_args()
        if not isinstance(self.min_value, self.types) or not isinstance(
                self.max_value, self.types
        ):
            error_msg = ('The min_value and max_value must be'
                         'types: %s' % self.types)
            raise Exception(error_msg)

    def _check_value_between(self):
        if isinstance(self._value, self.types
                      ) and (self._value < self.min_value
                             or self._value > self.max_value):
            error_msg = 'Field %s intput: %s, the value size is between：%s' % (
                self.key, self._value, (self.min_value, self.max_value))
            return [Exception(error_msg)]
        return []


class FloatCheckField(CheckField):
    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        self.min_value = min_value if min_value is not None else -float(
            sys.maxsize)
        self.max_value = max_value if max_value is not None else float(
            sys.maxsize)
        super(FloatCheckField, self).__init__(types=(float,), *args, **kwargs)

    def _check(self):
        return [
            *super(FloatCheckField, self)._check(),
            *self._check_value_between(),
        ]

    def _check_args(self):
        super(FloatCheckField, self)._check_args()
        if not isinstance(self.min_value, self.types) or not isinstance(
                self.max_value, self.types
        ):
            error_msg = ('The min_value and max_value must be'
                         'types: %s' % self.types)
            raise Exception(error_msg)

    def _check_value_between(self):
        if isinstance(self._value, self.types
                      ) and (self._value < self.min_value or
                             self._value > self.max_value):
            error_msg = 'Field %s input: %s, the value size is between：%s' % (
                self.key, self._value, (self.min_value, self.max_value))
            return [Exception(error_msg)]
        return []


class NumberCheckField(CheckField):
    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        self.min_value = min_value if min_value is not None else -sys.maxsize
        self.max_value = max_value if max_value is not None else sys.maxsize
        super(NumberCheckField, self).__init__(types=(int, float), *args,
                                               **kwargs)

    def _check(self):
        return [
            *super(NumberCheckField, self)._check(),
            *self._check_value_between(),
        ]

    def _check_args(self):
        super(NumberCheckField, self)._check_args()
        if not isinstance(self.min_value, self.types) or not isinstance(
                self.max_value, self.types
        ):
            error_msg = ('The min_value and max_value must be'
                         'types: %s' % self.types)
            raise Exception(error_msg)

    def _check_value_between(self):
        if isinstance(self._value, self.types
                      ) and (self._value < self.min_value
                             or self._value > self.max_value):
            error_msg = 'Field %s intput: %s, the value size is between：%s' % (
                self.key, self._value, (self.min_value, self.max_value))
            return [Exception(error_msg)]
        return []


class BooleanCheckField(CheckField):
    def __init__(self, *args, **kwargs):
        super(BooleanCheckField, self).__init__(types=(bool,), *args, **kwargs)


class ListCheckField(CheckField):
    def __init__(self, *args, **kwargs):
        super(ListCheckField, self).__init__(
            types=(list, tuple, set), *args, **kwargs)


class DictCheckField(CheckField):
    def __init__(self, *args, **kwargs):
        super(DictCheckField, self).__init__(types=(dict,), *args, **kwargs)


class DateCheckField(CheckField):
    def __init__(self, *args, **kwargs):
        super(DateCheckField, self).__init__(types=(
            datetime.date), *args, **kwargs)


class DateTimeCheckField(CheckField):
    def __init__(self, *args, **kwargs):
        super(DateTimeCheckField, self).__init__(types=(
            datetime.datetime), *args, **kwargs)


class TimeStampCheckField(CheckField):
    def __init__(self, unit='s', *args, **kwargs):
        self.unit = unit
        super(TimeStampCheckField, self).__init__(
            types=(int, str, datetime.datetime), *args, **kwargs
        )

    def _check_args(self):
        super(TimeStampCheckField, self)._check_args()
        if self.unit not in ['s', 'ms']:
            raise Exception('The timestamp unit must be s or ms')

    def format(self, value):
        if value is None:
            return
        elif isinstance(value, datetime.datetime):
            value = int(value.timestamp())
        elif isinstance(value, str):
            value = int(value)
        if self.unit == 'ms':
            return value * 1000
        return value


class MD5CheckField(StringCheckField):
    def __init__(self, *args, **kwargs):
        super(MD5CheckField, self).__init__(
            min_length=32, max_length=32, *args, **kwargs)


class IPCheckField(CheckField):
    IP_REGEX = (r'^((([1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5])\.)'
                r'{3}([1-9]|[1-9]\d|1\d{2}|2[0-4]\d|25[0-5]))$')

    def __init__(self, *args, **kwargs):
        super(IPCheckField, self).__init__(types=(
            str), *args, **kwargs)

    def _check_ip(self):
        if not self._type_checked:
            return []
        if not re.search(self.IP_REGEX, self._value):
            error_msg = 'Field %s input: %s, is not a ip' % self.key
            return [Exception(error_msg)]
        return []

    def _check(self):
        return [
            *super(IPCheckField, self)._check(),
            *self._check_ip(),
        ]


class URLCheckField(CheckField):
    URL_REGEX = (r'^(ftp|http|https):\/\/[\w-]+(\.[\w-]+)'
                 r'+([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?$')

    def __init__(self, *args, **kwargs):
        super(URLCheckField, self).__init__(types=(
            str), *args, **kwargs)

    def _check_url(self):
        if not self._type_checked or not self._value:
            return []
        if not re.search(self.URL_REGEX, self._value):
            error_msg = 'Field %s input: %s, is not a url' % (
                self.key, self._value)
            return [Exception(error_msg)]
        return []

    def _check(self):
        return [
            *super(URLCheckField, self)._check(),
            *self._check_url(),
        ]
