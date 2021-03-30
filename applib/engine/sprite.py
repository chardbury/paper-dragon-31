'''applib.animation -- animation classes

'''

import applib
import pyglet

from applib import app
from applib.engine import animation


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

    is_animating = False

    def animate_bounce(self, distance, speed=1.0):
        if not self.is_animating:
            animation.BounceAnimation(self, 'animation_offset_y', distance, speed).start()
            self.is_animating = True

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
