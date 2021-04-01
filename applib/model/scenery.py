'''applib.model.scenery -- static scenery objects

'''

import re

import applib
import pyglet

from applib.model import entity


class Scenery(entity.Entity):

    group = 'scenery'
    
    def get_layer(self):
        if 'background' in self.name:
            return -2
        return 0


def load_scenery():
    indexed_resources = list(pyglet.resource._default_loader._index)
    for resource_name in indexed_resources:
        if match := re.match(rf'{Scenery.group}/([a-z_]+)\.png', resource_name):
            asset_name = match.group(1)
            if asset_name not in entity.Entity.index[Scenery.group]:
                print(asset_name)
                class_name = ''.join(part.title() for part in re.split(r'_+', asset_name))
                scenery_class = type(class_name, (Scenery,), {'name': asset_name})
                globals()[class_name] = scenery_class

load_scenery()
del load_scenery
