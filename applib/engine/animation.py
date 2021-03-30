'''applib.animation -- animation classes

'''

import math

import applib
import pyglet

from applib import app
from applib.constants import TICK_LENGTH


class Animation(object):
    '''Base class for animations.

    '''

    next_animation = None
    
    def start(self):
        '''Ensure that the animation is active.

        '''
        if self not in app.animation:
            app.animation.append(self)
            self.start_state()
        return self

    def stop(self):
        '''Ensure that the animation is inactive.

        '''
        if self in app.animation:
            app.animation.remove(self)
            self.stop_state()
            if self.next_animation:
                self.next_animation.start()
        return self

    def queue(self, animation):
        '''Queue another animation after this chain.

        '''
        if self.next_animation is None:
            self.next_animation = animation
        else:
            self.next_animation.queue(animation)
        return self

    def start_state(self):
        '''Set the initial state of the animation.

        '''

    def stop_state(self):
        '''Set the final state of the animation.

        '''

    def tick(self):
        '''Advance the animation by a single tick.

        '''
        self.stop()


class AttributeAnimation(Animation):
    '''Animation class to update a single numerical attribute.

    '''

    _easing_names = {'linear', 'symmetric'}

    def __init__(self, thing, name, target, duration, easing='linear'):
        self.thing = thing
        self.name = name
        self.target = target
        self.duration = duration
        self.easing = easing
        self.original = None
        self.elapsed = None

    def interpolate(self):

        # Do the bounds check first.
        if self.elapsed <= 0.0:
            return self.original
        elif self.elapsed >= self.duration:
            return self.target

        # Pick a lerp based on the configured easing.
        lerp = self.elapsed / self.duration
        if self.easing == 'symmetric':
            lerp = 3.0 * (lerp ** 2) - 2.0 * (lerp ** 3)

        # Compute the interpolated value.
        lerp = max(0.0, min(1.0, lerp))
        return (1 - lerp) * self.original + lerp * self.target

    def start_state(self):
        self.original = getattr(self.thing, self.name)
        self.elapsed = 0.0

    def stop_state(self):
        setattr(self.thing, self.name, self.target)
        self.original = None
        self.elapsed = None

    def tick(self):
        self.elapsed += TICK_LENGTH
        if self.elapsed >= self.duration:
            self.stop()
        else:
            setattr(self.thing, self.name, self.interpolate())


class BounceAnimation(Animation):
    '''Animation class to cause an attribute to oscilate.

    '''

    def __init__(self, thing, name, distance, speed, cycles):
        self.thing = thing
        self.name = name
        self.distance = distance
        self.speed = speed
        self.cycles = cycles
        self.original = None
        self.elapsed = None

    def start_state(self):
        self.original = getattr(self.thing, self.name)
        self.elapsed = 0.0

    def stop_state(self):
        setattr(self.thing, self.name, self.original)
        self.original = None
        self.elapsed = None

    def tick(self):
        self.elapsed += TICK_LENGTH
        cycles_elapsed = self.speed * self.elapsed
        if (self.cycles is not None) and (cycles_elapsed >= self.cycles):
            self.stop()
        else:
            angular_distance = 2 * math.pi * cycles_elapsed
            linear_distance = self.distance * abs(math.sin(angular_distance))
            setattr(self.thing, self.name, self.original + linear_distance)


class WaitAnimation(Animation):
    '''Animation class to wait for a period of time and call a function.

    '''

    def __init__(self, duration, callback=None, *args, **kwargs):
        self.duration = duration
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def start_state(self):
        self.remaining = self.duration

    def stop_state(self):
        if self.callback is not None:
            self.callback(*self.args, **self.kwargs)

    def tick(self):
        self.remaining -= TICK_LENGTH
        if self.remaining <= 0.0:
            self.stop()


class QueuedAnimation(Animation):
    '''Animation class to run a sequence of queued animations.

    '''

    def __init__(self, *animations):
        self.animations = list(animations)
        self.remaining = None
        self.current = None

    def start_state(self):
        self.remaining = list(self.animations)
        self.current = None

    def stop_state(self):
        if self.current is not None:
            self.current.stop()
        for animation in self.remaining:
            animation.stop()
        self.remaining = None
        self.current = None

    def tick(self):
        if self.current not in app.animation:
            self.current = None
            if len(self.remaining) > 0:
                self.current = self.remaining.pop(0)
                self.current.start()
                self.current.tick()
            else:
                self.stop()


class ParallelAnimation(Animation):
    '''Animation class to run a collection of parallel animations.

    '''

    def __init__(self, *animations):
        self.animations = list(animations)
        self.remaining = None

    def start_state(self):
        self.remaining = list(self.animations)
        for animation in self.remaining:
            animation.start()

    def stop_state(self):
        for animation in self.remaining:
            animation.stop()
        self.remaining = None

    def tick(self):
        for animation in list(self.remaining):
            if animation not in app.animation:
                self.remaining.remove(animation)
        if len(self.remaining) == 0:
            self.stop()


class AnimationManager(list):

    def on_tick(self):
        '''Advance all current animations.

        '''
        for animation in list(self):
            animation.tick()
