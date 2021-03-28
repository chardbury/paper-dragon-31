'''applib.animation -- animation classes

'''

import logging

import applib
import pyglet

from applib import app
from applib.constants import TICK_LENGTH

_logger = logging.getLogger(__name__)


class Animation(object):
    '''Base class for animations.

    '''

    def start(self):
        '''Ensure that the animation is active.

        '''
        if self not in animation_manager.current_animations:
            animation_manager.current_animations.append(self)

    def stop(self):
        '''Ensure that the animation is inactive.

        '''
        if self in animation_manager.current_animations:
            animation_manager.current_animations.remove(self)

    def update(self, delta):
        '''Advance the animation by the given amount of time.

        '''
        self.stop()


class AttributeAnimation(Animation):
    '''Animation class to update a single numerical attribute.

    '''

    def __init__(self, thing, name, target, speed):
        self.thing = thing
        self.name = name
        self.target = target
        self.speed = speed

    def tick(self):
        current_value = getattr(self.thing, self.name)
        if current_value <= self.target:
            new_value = current_value + self.speed * TICK_LENGTH
            if new_value >= self.target:
                setattr(self.thing, self.name, self.target)
                self.stop()
            else:
                setattr(self.thing, self.name, new_value)
        if current_value >= self.target:
            new_value = current_value - self.speed * TICK_LENGTH
            if new_value <= self.target:
                setattr(self.thing, self.name, self.target)
                self.stop()
            else:
                setattr(self.thing, self.name, new_value)


class WaitAnimation(Animation):
    '''Animation class to wait for a period of time.

    '''

    def __init__(self, duration):
        self.duration = duration
        self.remaining = duration

    def tick(self):
        self.remaining -= TICK_LENGTH
        if self.remaining <= 0.0:
            self.stop()


class QueuedAnimation(Animation):
    '''Animation class to run a sequence of queued animations.

    '''

    def __init__(self, *animations):
        self.animations = list(animations)
        self.current = None

    def tick(self):
        if self.current not in animation_manager.current_animations:
            if len(self.animations) > 0:
                self.current = self.animations.pop(0)
                self.current.start()
                self.current.tick()
            else:
                self.stop()


class AnimationManager(object):


    def __init__(self):
        '''Construct an AnimationManager object.

        '''
        self.current_animations = []

    def on_tick(self):
        '''Advance all current animations.

        '''
        for animation in list(self.current_animations):
            animation.tick()


animation_manager = AnimationManager()
