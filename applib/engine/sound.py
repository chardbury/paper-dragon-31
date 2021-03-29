'''applib.engine.sound -- sound effects library

'''

import random
import re

import applib
import pyglet

from applib import app


class Sound(object):

    def __init__(self):
        self.sources = []

    def add(self, source_name):
        source = pyglet.resource.media(f'sounds/{source_name}.mp3', streaming=False)
        self.sources.append(source)

    def __call__(self):
        player = random.choice(self.sources).play()
        player.volume = app.settings.volume


def load_sounds():
    indexed_resources = list(pyglet.resource._default_loader._index)
    for resource_name in indexed_resources:
        if match := re.match(rf'sounds/(([a-z_]+)(?:_[0-9]+)?)\.mp3', resource_name):
            asset_name, sound_name = match.groups()
            assert re.match(r'__', asset_name) is None
            globals().setdefault(sound_name, Sound()).add(asset_name)

load_sounds()
del load_sounds
