'''applib.model.entity -- generic model objects

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


class Entity(object):

    #: The asset group to which the entity class belongs.
    group = None

    #: The name of the entity class within its asset group.
    name = None

    #: The texture used to render entities of this class.
    texture = None

    #: The global index of all entity classes.
    index = {}

    def __init_subclass__(cls):
        '''Create an `Entity` subclass.

        '''
        if cls.group is not None:
            cls.group = _normalise(cls.group)
        if cls.name is not None:
            cls.name = _normalise(cls.name)
        if (cls.group is not None) and (cls.name is not None):
            cls.texture = pyglet.resource.texture(f'{cls.group}/{cls.name}.png')
            cls.index[f'{cls.group}/{cls.name}'] = cls

    def __init__(self, level):
        '''Create an `Entity` object.

        '''
        self.level = level
        self.create_sprite()

    def create_sprite(self):
        if self.texture is not None:
            self.sprite = pyglet.sprite.Sprite(self.texture)

    def tick(self):
        pass
