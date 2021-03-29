'''applib.engine.sound -- sound effects library

'''

import re

import applib
import pyglet

from applib import app


class Sound(object):

    def __init__(self, name):
        self.source = pyglet.resource.media(f'sounds/{name}.mp3', streaming=False)

    def __call__(self):
        player = self.source.play()
        player.volume = app.settings.volume


def load_sounds():
    indexed_resources = list(pyglet.resource._default_loader._index)
    for resource_name in indexed_resources:
        if match := re.match(rf'sounds/([a-z_]+)\.mp3', resource_name):
            asset_name = match.group(1)
            assert re.match(r'__', asset_name) is None
            globals()[asset_name] = Sound(asset_name)

load_sounds()
del load_sounds
