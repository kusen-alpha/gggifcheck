# gggifcheck

通用条目字段检查(General General General Item Field Check)
，是基于Python编写通用检查工具，适应于各种场景的使用，只需要略微进行适配。

## 使用方法

### 安装

    pip install gggifcheck

### 使用CheckField

```python
from gggifcheck.fields import StringCheckField

# 方式1
s = StringCheckField(key='s', value='aa', min_length=1, max_length=2,
                     contains=['a'], excludes=['b'])
print(s.value)
# 方式2
s = StringCheckField(min_length=1, max_length=2, contains=['a'], excludes=['b'])
s.input('s', 'aa')
print(s.value)
```
    
### 使用CheckItem

```python
from gggifcheck.fields import StringCheckField
from gggifcheck.items import CheckItem


class TestCheckItem(CheckItem):
    a = StringCheckField(min_length=1, max_length=2, contains=['a'],
                         excludes=['b'])
    b = StringCheckField(min_length=1, max_length=2, contains=['a'],
                         excludes=['c'])


item = TestCheckItem()
item['a'] = 'aa'
item['b'] = 'ab'
print(dict(item))
```

## 使用案例

### 结合scrapy

```python
# 对scrapy Item进行改写
import scrapy
from gggifcheck import fields
from gggifcheck.items import CheckItem, BuildCheckField


class ScrapyCheckItem(scrapy.Item, CheckItem):

    def __init__(self, *args, **kwargs):
        self._values = {}
        self.check_fields = {}
        if args or kwargs:
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def __getitem__(self, key):
        if key in self.fields and key not in self._values:
            value = None
            for field1, field2 in self.relate_process_default:
                value = self[field2]
                break
            self[key] = value
        return self._values[key]

    def __setitem__(self, key, value):
        if key in self.fields:
            field = self.fields[key]
            build_check_field = field.get('build_check_field')
            if build_check_field:
                check_field = build_check_field.build(key=key, value=value)
                self.check_fields[key] = check_field
                self._values[key] = check_field.value
            else:
                self._values[key] = value
        else:
            raise KeyError(
                f"{self.__class__.__name__} does not support field: {key}")

    def __setattr__(self, name, value):
        if name.startswith('_') or name in ['check_fields']:
            self.__dict__[name] = value
        else:
            raise AttributeError(
                f"Use item[{name!r}] = {value!r} to set field value")

    def check_all(self):
        """
        进行所有字段检查
        :return:
        """
        self._process_and_check()
        _ = [self[field] for field in self.fields]

    def keys(self):
        # 不能放在此处验证的原因是scrapy item进入pipeline前有日志打印等操作导致进行
        # 此处验证，导致如果在pipeline里进行透传时验证不生效，提前检查报错，此处验证放
        # 在check_all方法中，因此需要手动调用
        # self._process_and_check()
        # _ = [self[field] for field in self.fields]  # 进行所有字段检查
        return self._values.keys()

    def get_base_value(self, key):
        if key in self.check_fields:
            return self.check_fields[key].base_value
        elif key in self.fields:
            field = self.fields[key]
            build_check_field = field.get('build_check_field')
            if build_check_field:
                return build_check_field.build_default(
                    key=key, value=None).base_value
            return self.fields[key] or None
        else:
            raise KeyError(
                f"{self.__class__.__name__} does not support field: {key}")


# 示例
class PostItem(ScrapyCheckItem):
    id = scrapy.Field(
        build_check_field=BuildCheckField(
            check_field_class=fields.MD5CheckField, nullable=False))
    channel = scrapy.Field(
        build_check_field=BuildCheckField(
            check_field_class=fields.IntegerCheckField,
            nullable=False, min_value=1, max_value=6))


item = PostItem()
item['id'] = '81dc9bdb52d04dc20036dbd8313ed055'
item['channel'] = 1
print(dict(item))
```

## 关于作者

1. 邮箱：1194542196@qq.com
2. 微信：hu1194542196
3. 目前还需要很多需要改进的地方，可以私信作者，你们的提供越多，本库才能更完善。