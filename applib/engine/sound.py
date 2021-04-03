'''applib.engine.sound -- sound effects library

'''

import os
import random
import re

import applib
import pyglet

from applib import app


class Sound(object):

    sounds = []

    def __init__(self):
        self.sounds.append(self)
        self.sources = []

    @classmethod
    def _preload(cls, delta=None):
        for sound in cls.sounds:
            for source in sound.sources:
                source = pyglet.resource.media(source, streaming=True)
                source.play().volume = 0.0

    def add(self, source_name):
        if len(os.environ.get('PYTEST_CURRENT_TEST', '')) > 0: return
        source = f'sounds/{source_name}.mp3'
        self.sources.append(source)

    def __call__(self):
        if len(os.environ.get('PYTEST_CURRENT_TEST', '')) > 0: return
        source = random.choice(self.sources)
        source = pyglet.resource.media(source, streaming=True)
        player = source.play()
        player.volume = app.settings.sound_volume * app.settings.volume
        return player


def load_sounds():
    indexed_resources = list(pyglet.resource._default_loader._index)
    for resource_name in indexed_resources:
        if match := re.match(rf'sounds/(([a-z_]+)(?:_[0-9]+)?)\.(?:mp3|ogg)', resource_name):
            asset_name, sound_name = match.groups()
            assert re.match(r'__', asset_name) is None
            globals().setdefault(sound_name, Sound()).add(asset_name)

load_sounds()
del load_sounds

#Sound._preload()
#pyglet.clock.schedule_once(Sound._preload, 0.0)
