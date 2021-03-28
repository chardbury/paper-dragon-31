'''applib.model.item -- movable items

'''

import re

import applib
import pyglet


def _normalise(string):
    '''Normalise the given string.

    '''
    string = string.strip().lower()
    string = re.sub(r'\s+', '_', string)
    string = re.sub(r'[^a-z_]', '', string)
    return string


class Item(object):

    _all = {}

    def __init__(self, name):
        self.name = _normalise(name)
        self.image = pyglet.resource.image(f'items/{self.name}.png')

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @classmethod
    def get(cls, name):
        name = _normalise(name)
        if name not in cls._all:
            cls._all[name] = cls(name)
        return cls._all[name]

get = Item.get


## Actual Items

for _item_name in [
    'batter',
    'doughnut',
    'doughnut_cooked',
    'better doughnut',
]:
    Item.get(_item_name)
