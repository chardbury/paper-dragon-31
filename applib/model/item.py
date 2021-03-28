'''applib.model.item -- movable items

'''

import re

import applib
import pyglet


def _normalize(string):
    string = string.strip().lower()
    string = re.sub(r'\s+', '_', string)
    string = re.sub(r'[^a-z_]', '', string)
    return string


class Item(object):

    _all = {}

    def __init__(self, name):
        self.name = _normalize(name)
        self.image = pyglet.resource.image(f'items/{self.name}.png')

    def __eq__(self, other):
        return self.name == other.name

    @classmethod
    def get(cls, name):
        name = _normalize(name)
        if name not in cls._all:
            cls._all[name] = cls(name)
        return cls._all[name]

get = Item.get


## Actual Items

for _item_name in [
    'batter',
    'doughnut',
    'better doughnut',
]:
    Item.get(_item_name)
