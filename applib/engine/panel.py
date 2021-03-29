'''applib.engine.panel -- extremely basic interface panel

'''

import applib
import pyglet

from applib import app

from pyglet.gl import *


class Panel(object):

    def __init__(self,
        align_x = 0.5,
        align_y = 0.5,
        width = 1.0,
        height = 1.0,
        aspect = None,
        background = None,
        sprites = (),
        ):

        # Attributes
        self.align_x = align_x
        self.align_y = align_y
        self.width = width
        self.height = height
        self.aspect = aspect
        self.background = background
        self.sprites = list(sprites)

        # Hierarchy
        self._parent = None
        self._children = []

    # Hierarchy

    def add(self, panel=None, **kwargs):
        panel = Panel if (panel is None) else panel
        if not isinstance(panel, Panel):
            panel = panel(**kwargs)
        self._children.append(panel)
        panel._parent = self
        return panel

    # Dimensions

    def get_size(self):
        parent_width, parent_height = self.get_parent_size()
        width = self.width * parent_width
        height = self.height * parent_height
        if self.aspect is not None:
            aspect_x, aspect_y = self.aspect
            if aspect_x * height > aspect_y * width:
                height = aspect_y * width / aspect_x
            elif aspect_y * width > aspect_x * height:
                width = aspect_x * height / aspect_y
        return width, height

    def get_parent_size(self):
        if self._parent is None:
            return (
                app.window.width,
                app.window.height,
            )
        return self._parent.get_size()

    def get_offset(self):
        w, h = self.get_size()
        pw, ph = self.get_parent_size()
        return (
            self.align_x * (pw - w),
            self.align_y * (ph - h),
        )

    # Rendering

    def draw(self, draw_x=0.0, draw_y=0.0):
        offset_x, offset_y = self.get_offset()
        width, height = self.get_size()
        draw_x += offset_x
        draw_y += offset_y

        # Render background
        if self.background is not None:
            pyglet.graphics.draw(4, pyglet.gl.GL_TRIANGLE_STRIP,
                ('v2f', [
                    draw_x, draw_y,
                    draw_x + width, draw_y,
                    draw_x, draw_y + height,
                    draw_x + width, draw_y + height,
                ]),
                ('c4B', list(self.background) * 4),
            )

        # Render sprites
        if len(self.sprites) > 0:
            glPushMatrix()
            glTranslatef(draw_x, draw_y, 0.0)
            for sprite in self.sprites:
                sprite.draw()
            glPopMatrix()

        # Render children
        for child in self._children:
            child.draw(draw_x, draw_y)
