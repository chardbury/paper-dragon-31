'''applib.model.item -- movable items

'''

import re

import applib
import pyglet

from applib.model import entity


class Item(entity.Entity):

    group = 'items'

    def __eq__(self, other):
        return type(self) == type(other)
    
    def __hash__(self):
        return hash(type(self))


def load_items():
    indexed_resources = list(pyglet.resource._default_loader._index)
    for resource_name in indexed_resources:
        if match := re.match(rf'{Item.group}/([a-z_]+)\.png', resource_name):
            asset_name = match.group(1)
            if asset_name not in entity.Entity.index[Item.group]:
                class_name = ''.join(part.title() for part in re.split(r'_+', asset_name))
                item_class = type(class_name, (Item,), {'name': asset_name})
                globals()[class_name] = item_class

load_items()
del load_items
