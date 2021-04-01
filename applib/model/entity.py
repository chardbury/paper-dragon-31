'''applib.model.entity -- generic model objects

'''

import re

import applib
import pyglet

from applib.engine import sprite


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

    #: The global index of all entity classes.
    index = {}

    def __init_subclass__(cls):
        '''Create an `Entity` subclass.

        '''
        if cls.group is not None:
            cls.group = _normalise(cls.group)
            cls.index.setdefault(cls.group, {})
        if cls.name is not None:
            cls.name = _normalise(cls.name)
            cls.index[cls.group][cls.name] = cls


    def __init__(self, level):
        '''Create an `Entity` object.

        '''
        self.level = level
        if self.level is not None:
            self.level.add_entity(self)

    def destroy(self):
        '''Remove the entity from its level.

        '''
        if self.level is not None:
            self.level.remove_entity(self)
        self.level = None

    #: The texture used to render entities of this class.
    _texture = None

    @property
    def texture(self):
        if (self._texture is None) and (self.group is not None) and (self.name is not None):
            type(self)._texture = pyglet.resource.texture(f'{self.group}/{self.name}.png')
        return self._texture

    #: The sprite used to render entities of this class (default value).
    _sprite = None

    @property
    def sprite(self):
        if (self._sprite is None) and (self.texture is not None):
            self._sprite = sprite.EntitySprite(self.texture)
        return self._sprite

    def tick(self):
        pass
