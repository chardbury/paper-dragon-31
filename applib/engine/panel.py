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
        text = None,
        text_color = (255, 255, 255, 255),
        font_name = 'Lato',
        font_size = 0.1
        ):

        # Attributes
        self.align_x = align_x
        self.align_y = align_y
        self.width = width
        self.height = height
        self.aspect = aspect
        self.background = background
        self.sprites = list(sprites)

        # Text
        self.text = text
        self.text_color = text_color
        self.font_name = font_name
        self.font_size = font_size

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

    def get_default_size(self):
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
        return self._parent.get_content_size()

    def get_root_size(self):
        if self._parent is None:
            return self.get_content_size()
        return self._parent.get_root_size()

    def get_offset(self):
        w, h = self.get_content_size()
        pw, ph = self.get_parent_size()
        return (
            self.align_x * (pw - w),
            self.align_y * (ph - h),
        )

    ## Content

    content_types = []

    def get_content_size(self):
        for content_type, size_method, offset_method in self.content_types:
            if getattr(self, content_type):
                return getattr(self, size_method)()
        return self.get_default_size()

    def get_content_offset(self):
        for content_type, size_method, offset_method in self.content_types:
            if getattr(self, content_type):
                return getattr(self, offset_method)()
        return self.get_default_offset()

    ## Content : Text

    content_types.append(('text', 'get_text_size', 'get_text_offset'))

    _text_document = None

    _text_layout = None

    def get_text_size(self):
        self._text_document = pyglet.text.document.UnformattedDocument()
        self._text_layout = pyglet.text.layout.IncrementalTextLayout(self._text_document, 0, 0)
        self._text_layout.begin_update()
        self._text_layout.content_width = 0 # Do not remove this line... seriously!
        self._text_document.set_style(0, 0, {
            "font_name" : self.font_name,
            "font_size" : int(self.font_size * self.get_root_size()[1]),
            "color" : [min(255, int(256 * channel)) for channel in self.text_color],
            "align" : "center"})
        self._text_document.text = self.text
        self._text_layout.x = self._text_layout.y = 0
        self._text_layout.width = self.get_default_size()[0]
        self._text_layout.height = self.get_default_size()[1]
        self._text_layout.content_valign = "bottom"
        self._text_layout.multiline = False
        self._text_layout.end_update()
        self._text_layout.begin_update()
        self._text_layout.width = self._text_layout.content_width
        self._text_layout.height = self._text_layout.content_height
        self._text_layout.end_update()
        return (self._text_layout.content_width,
                self._text_layout.content_height)

    def get_text_offset(self):
        pass


    # Rendering

    def draw(self, draw_x=0.0, draw_y=0.0):
        offset_x, offset_y = self.get_offset()
        width, height = self.get_content_size()
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

        if self.text:
            self._text_layout.x = draw_x
            self._text_layout.y = draw_y
            self._text_layout.draw()

        # Render children
        for child in self._children:
            child.draw(draw_x, draw_y)
