'''applib.animation -- animation classes

'''

import math
import random

import applib
import pyglet

from applib import app
from applib.engine import animation
from applib.constants import TICK_LENGTH


class WalkAnimation(animation.Animation):

    def __init__(self, sprite, walk_speed, bounce_distance, bounce_speed):
        self.sprite = sprite
        self.walk_speed = walk_speed
        self.bounce_distance = bounce_distance
        self.bounce_speed = bounce_speed
        self.bounce_cycles = None
        self.elapsed_time = None

    def start_state(self):
        self.bounce_cycles = None
        self.elapsed_time = 0.0

    def stop_state(self):
        self.bounce_cycles = None
        self.elapsed_time = None

    def tick(self):
        self.elapsed_time += TICK_LENGTH

        # Compute the horizontal offset.
        current_x = self.sprite.animation_offset_x
        target_x = self.sprite.walk_target
        if target_x > current_x:
            current_x += self.walk_speed * TICK_LENGTH
            if target_x <= current_x:
                current_x = target_x
        elif target_x < current_x:
            current_x -= self.walk_speed * TICK_LENGTH
            if target_x >= current_x:
                current_x = target_x
        setattr(self.sprite, 'animation_offset_x', current_x)

        # Compute the vertical offset.
        cycles_elapsed = self.bounce_speed * self.elapsed_time
        angular_distance = 2 * math.pi * cycles_elapsed
        relative_distance = abs(math.sin(angular_distance))
        linear_distance = self.bounce_distance * relative_distance
        if target_x == current_x:
            if self.bounce_cycles is None:
                self.bounce_cycles = math.ceil(cycles_elapsed) + 1.0
            elif self.bounce_cycles <= cycles_elapsed:
                linear_distance = 0.0
        else:
            if self.bounce_cycles is not None:
                self.bounce_cycles = None
        setattr(self.sprite, 'animation_offset_y', linear_distance)


class AnimatedSprite(pyglet.sprite.Sprite):

    # Property: `animation_offset_x`
    
    _animation_offset_x = 0

    @property
    def animation_offset_x(self):
        return self._animation_offset_x

    @animation_offset_x.setter
    def animation_offset_x(self, value):
        self._animation_offset_x = value
        self._update_position()

    # Property: `animation_offset_y`
    
    _animation_offset_y = 0

    @property
    def animation_offset_y(self):
        return self._animation_offset_y

    @animation_offset_y.setter
    def animation_offset_y(self, value):
        self._animation_offset_y = value
        self._update_position()

    # Animation Methods

    current_animation = None

    def queue_animation(self, animation):
        if self.current_animation is None:
            self.current_animation = animation.start()
        else:
            self.current_animation.queue(animation)

    def stop_animation(self):
        if self.current_animation is not None:
            self.current_animation.stop()
            self.current_animation = None

    # Update Position Method

    def _update_position(self):
        img = self._texture
        scale_x = self._scale * self._scale_x
        scale_y = self._scale * self._scale_y
        if not self._visible:
            vertices = (0, 0, 0, 0, 0, 0, 0, 0)
        elif self._rotation:
            x1 = -img.anchor_x * scale_x
            y1 = -img.anchor_y * scale_y
            x2 = x1 + img.width * scale_x
            y2 = y1 + img.height * scale_y
            x = self._x + self.animation_offset_x
            y = self._y + self.animation_offset_y
            r = -math.radians(self._rotation)
            cr = math.cos(r)
            sr = math.sin(r)
            ax = x1 * cr - y1 * sr + x
            ay = x1 * sr + y1 * cr + y
            bx = x2 * cr - y1 * sr + x
            by = x2 * sr + y1 * cr + y
            cx = x2 * cr - y2 * sr + x
            cy = x2 * sr + y2 * cr + y
            dx = x1 * cr - y2 * sr + x
            dy = x1 * sr + y2 * cr + y
            vertices = (ax, ay, bx, by, cx, cy, dx, dy)
        elif scale_x != 1.0 or scale_y != 1.0:
            x1 = self._x + self.animation_offset_x - img.anchor_x * scale_x
            y1 = self._y + self.animation_offset_y - img.anchor_y * scale_y
            x2 = x1 + img.width * scale_x
            y2 = y1 + img.height * scale_y
            vertices = (x1, y1, x2, y1, x2, y2, x1, y2)
        else:
            x1 = self._x + self.animation_offset_x - img.anchor_x
            y1 = self._y + self.animation_offset_y - img.anchor_y
            x2 = x1 + img.width
            y2 = y1 + img.height
            vertices = (x1, y1, x2, y1, x2, y2, x1, y2)
        if not self._subpixel:
            vertices = (int(vertices[0]), int(vertices[1]),
                        int(vertices[2]), int(vertices[3]),
                        int(vertices[4]), int(vertices[5]),
                        int(vertices[6]), int(vertices[7]))
        self._vertex_list.vertices[:] = vertices
