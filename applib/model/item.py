'''applib.model.item -- movable items

'''

import re

import applib
import pyglet

from applib.model import entity


class Item(entity.Entity):

    group = 'items'

    holds = None

    holds_position = None

    def destroy(self):
        if self.holds is not None:
            self.holds.destroy()
        super().destroy()
    
    def matches(self, other):
        return type(self) is type(other)


class Time(Item):
    pass


class Plate(Item):

    name = 'plate'

    holds_position = (0.0, 0.2)


def load_items():
    indexed_resources = list(pyglet.resource._default_loader._index)
    for resource_name in indexed_resources:
        if match := re.match(rf'{Item.group}/([A-Za-z_]+)\.png', resource_name):
            asset_name = match.group(1)
            if asset_name not in entity.Entity.index[Item.group]:
                class_name = ''.join(part.title() for part in re.split(r'_+', asset_name))
                if class_name not in globals():
                    item_class = type(class_name, (Item,), {'name': asset_name})
                    globals()[class_name] = item_class

load_items()
del load_items
