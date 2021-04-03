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
        anchor_x = None,
        anchor_y = None,
        width = 1.0,
        height = 1.0,
        padding = 0.0,
        aspect = None,
        frame_texture = None,
        frame_width = 0.04,
        background_color = None,
        background_texture = None,
        sprites = (),
        text = None,
        text_color = (255, 255, 255, 255),
        text_bold = False,
        text_wrap = False,
        font_name = 'Fredoka One',
        font_size = 0.1,
        image_texture = None,
        image_color = (255, 255, 255, 255),
        image_flip_x = False,
        draw_function = None,
        visible = True,
        ):

        # Attributes
        self.align_x = align_x
        self.align_y = align_y
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.width = width
        self.height = height
        self.padding = padding
        self.aspect = aspect
        self.frame_texture = frame_texture
        self.frame_width = frame_width
        self.background_color = background_color
        self.background_texture = background_texture
        self.sprites = list(sprites)
        self.draw_function = draw_function
        self.visible = visible

        # Text
        self.text = text
        self.text_color = text_color
        self.text_bold = text_bold
        self.text_wrap = text_wrap
        self.font_name = font_name
        self.font_size = font_size

        # Image
        self.image_texture = image_texture
        self.image_color = image_color
        self.image_flip_x = image_flip_x

        # Hierarchy
        self._parent = None
        self._children = []

        self._background_opacity = None

    @property
    def background_opacity(self):
        if self._background_opacity is None:
            self._background_opacity = self.background_color[3] / 255
        return self._background_opacity
    
    @background_opacity.setter
    def background_opacity(self, value):
        self._background_opacity = value
        self.background_color = list(self.background_color)
        self.background_color[3] = max(0, min(255, int(256 * self._background_opacity)))

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
        padding = self.padding * parent_height
        width = self.width * parent_width - 2 * padding
        height = self.height * parent_height - 2 * padding
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
        width, height = self.get_content_size()
        parent_width, parent_height = self.get_parent_size()
        padding = self.padding * parent_height
        anchor_x = self.anchor_x if self.anchor_x is not None else self.align_x
        anchor_y = self.anchor_y if self.anchor_y is not None else self.align_y
        return (
            self.align_x * parent_width - anchor_x * width,
            self.align_y * parent_height - anchor_y * height,
        )

    ## Content

    content_types = []

    def get_content_size(self):
        for content_type, size_method, draw_method in self.content_types:
            if getattr(self, content_type):
                return getattr(self, size_method)()
        return self.get_default_size()

    ## Content : Text

    content_types.append(('text', 'get_text_size', 'draw_text'))

    _text_document = None

    _text_layout = None

    def text_update(self, text):
        self.text = text
        self._text_layout = None

    def get_text_size(self):
        if self._text_layout is None:
            default_width, default_height = self.get_default_size()
            root_width, root_height = self.get_root_size()

            self._text_document = pyglet.text.document.UnformattedDocument()
            self._text_layout = pyglet.text.layout.IncrementalTextLayout(self._text_document, 0, 0)

            self._text_layout.begin_update()
            self._text_layout.content_width = 0 # Do not remove this line... seriously!
            self._text_document.set_style(0, 0, {
                'font_name': self.font_name,
                'font_size': int(self.font_size * root_height),
                'color': self.text_color,
                'align': 'left',
                'bold': self.text_bold,
            })
            self._text_document.text = self.text
            self._text_layout.x = self._text_layout.y = 0
            self._text_layout.width = default_width
            self._text_layout.height = default_height
            self._text_layout.content_valign = 'bottom'
            self._text_layout.multiline = True
            self._text_layout.wrap_lines = self.text_wrap
            self._text_layout.end_update()

            self._text_layout.width = self._text_layout.content_width + 1
            self._text_layout.height = self._text_layout.content_height + 1

        return (self._text_layout.content_width,
                self._text_layout.content_height)

    def draw_text(self, draw_x, draw_y):
        self._text_layout.x = draw_x
        self._text_layout.y = draw_y
        self._text_layout.draw()

    ## Content : Image

    content_types.append(('image_texture', 'get_image_size', 'draw_image'))

    def get_image_size(self):
        default_width, default_height = self.get_default_size()
        texture_width = self.image_texture.width
        texture_height = self.image_texture.height
        image_width = default_width
        image_height = default_height
        if texture_height * default_width > default_height * texture_width:
            image_width = default_height * texture_width / texture_height
        else:
            image_height = default_width * texture_height / texture_width
        return image_width, image_height

    def draw_image(self, draw_x, draw_y):
        width, height = self.get_content_size()
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(self.image_texture.target)
        glBindTexture(self.image_texture.target, self.image_texture.id)
        tx = list(self.image_texture.tex_coords)
        if self.image_flip_x:
            tx[0], tx[3] = tx[3], tx[0]
            tx[6], tx[9] = tx[9], tx[6]
        verts = [
            draw_x, draw_y,
            draw_x + width, draw_y,
            draw_x + width, draw_y + height,
            draw_x, draw_y + height,
        ]
        vertes = list(map(int, verts))
        pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
            ('v2f', verts),
            ('t3f', tx),
            ('c4B', list(self.image_color) * 4),
        )
        glPopAttrib()

    # Events

    def contains(self, x, y):
        corner_x, corner_y = 0.0, 0.0
        current_panel = self
        while current_panel is not None:
            offset_x, offset_y = current_panel.get_offset()
            current_panel = current_panel._parent
            corner_x += offset_x
            corner_y += offset_y
        width, height = self.get_content_size()
        return (0 <= x - corner_x < width) and (0 <= y - corner_y < height)


    # Rendering

    def draw(self, draw_x=0.0, draw_y=0.0):
        if not self.visible:
            return
        offset_x, offset_y = self.get_offset()
        width, height = self.get_content_size()
        parent_width, parent_height = self.get_parent_size()
        padding = self.padding * parent_height
        draw_x += offset_x
        draw_y += offset_y

        # Render background
        if self.background_texture is not None:
            tex_coords = self.background_texture.tex_coords
            frame_width = self.frame_width * parent_height
            vertex_data = [
                # Bottom-left corner
                draw_x - padding - frame_width, draw_y - padding - frame_width,
                draw_x - padding, draw_y - padding - frame_width,
                draw_x - padding - frame_width, draw_y - padding,
                draw_x - padding, draw_y - padding,
                # Bottom-right corner
                draw_x + padding + width, draw_y - padding - frame_width,
                draw_x + padding + width + frame_width, draw_y - padding - frame_width,
                draw_x + padding + width, draw_y - padding,
                draw_x + padding + width + frame_width, draw_y - padding,
                # Top-left corner
                draw_x - padding - frame_width, draw_y + padding + height,
                draw_x - padding, draw_y + padding + height,
                draw_x - padding - frame_width, draw_y + padding + height + frame_width,
                draw_x - padding, draw_y + padding + height + frame_width,
                # Top-right corner
                draw_x + padding + width, draw_y + padding + height,
                draw_x + padding + width + frame_width, draw_y + padding + height,
                draw_x + padding + width, draw_y + padding + height + frame_width,
                draw_x + padding + width + frame_width, draw_y + padding + height + frame_width,
            ]
            tx1, ty1 = tex_coords[0:2]
            tx2, ty2 = tex_coords[6:8]
            txm = (tx1 + tx2) / 2
            tym = (ty1 + ty2) / 2
            texture_data = [
                # Bottom-left corner
                tx1, ty1, txm, ty1, tx1, tym, txm, tym,
                # Bottom-right corner
                txm, ty1, tx2, ty1, txm, tym, tx2, tym,
                # Top-left corner
                tx1, tym, txm, tym, tx1, ty2, txm, ty2,
                # Top-right corner
                txm, tym, tx2, tym, txm, ty2, tx2, ty2,
            ]
            glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
            glEnable(self.background_texture.target)
            glBindTexture(self.background_texture.target, self.background_texture.id)
            color = self.background_color or (255, 255, 255, 255)
            pyglet.graphics.draw_indexed(16, GL_TRIANGLE_STRIP,
                [0, 1, 2, 3, 8, 9, 10, 9, 11, 9, 14, 12, 15, 12, 13, 12, 7, 6, 5, 6, 4, 6, 1, 3, 3, 6, 9, 12],
                ('v2f', vertex_data), ('t2f', texture_data), ('c4B', color * 16))
            glPopAttrib()
        elif self.background_color is not None:
            color = self.background_color or [255, 255, 255, 255]
            extra_width = padding + self.frame_width * parent_height / 2
            data = [
                ('v2f', [
                    draw_x - extra_width, draw_y - extra_width,
                    draw_x + extra_width + width, draw_y - extra_width,
                    draw_x - extra_width, draw_y + extra_width + height,
                    draw_x + extra_width + width, draw_y + extra_width + height,
                ]),
                ('c4B', list(color) * 4),
            ]
            pyglet.graphics.draw(4, pyglet.gl.GL_TRIANGLE_STRIP, *data)

        # Render sprites
        if len(self.sprites) > 0:
            glPushMatrix()
            glTranslatef(draw_x, draw_y, 0.0)
            for sprite in self.sprites:
                sprite.draw()
            glPopMatrix()

        # Render content
        for content_type, size_method, draw_method in self.content_types:
            if getattr(self, content_type):
                getattr(self, draw_method)(draw_x, draw_y)
        if self.draw_function is not None:
            self.draw_function(draw_x, draw_y)

        # Render children
        for child in self._children:
            child.draw(draw_x, draw_y)

        # Render frame
        if self.frame_texture is not None:
            tex_coords = self.frame_texture.tex_coords
            frame_width = self.frame_width * parent_height
            vertex_data = [
                # Bottom-left corner
                draw_x - padding - frame_width, draw_y - padding - frame_width,
                draw_x - padding, draw_y - padding - frame_width,
                draw_x - padding - frame_width, draw_y - padding,
                draw_x - padding, draw_y - padding,
                # Bottom-right corner
                draw_x + padding + width, draw_y - padding - frame_width,
                draw_x + padding + width + frame_width, draw_y - padding - frame_width,
                draw_x + padding + width, draw_y - padding,
                draw_x + padding + width + frame_width, draw_y - padding,
                # Top-left corner
                draw_x - padding - frame_width, draw_y + padding + height,
                draw_x - padding, draw_y + padding + height,
                draw_x - padding - frame_width, draw_y + padding + height + frame_width,
                draw_x - padding, draw_y + padding + height + frame_width,
                # Top-right corner
                draw_x + padding + width, draw_y + padding + height,
                draw_x + padding + width + frame_width, draw_y + padding + height,
                draw_x + padding + width, draw_y + padding + height + frame_width,
                draw_x + padding + width + frame_width, draw_y + padding + height + frame_width,
            ]
            vertex_data = list(map(int, vertex_data))
            tx1, ty1 = tex_coords[0:2]
            tx2, ty2 = tex_coords[6:8]
            txm = (tx1 + tx2) / 2
            tym = (ty1 + ty2) / 2
            texture_data = [
                # Bottom-left corner
                tx1, ty1, txm, ty1, tx1, tym, txm, tym,
                # Bottom-right corner
                txm, ty1, tx2, ty1, txm, tym, tx2, tym,
                # Top-left corner
                tx1, tym, txm, tym, tx1, ty2, txm, ty2,
                # Top-right corner
                txm, tym, tx2, tym, txm, ty2, tx2, ty2,
            ]
            glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
            glEnable(self.frame_texture.target)
            glBindTexture(self.frame_texture.target, self.frame_texture.id)
            pyglet.graphics.draw_indexed(16, GL_TRIANGLE_STRIP,
                [0, 1, 2, 3, 8, 9, 10, 9, 11, 9, 14, 12, 15, 12, 13, 12, 7, 6, 5, 6, 4, 6, 1, 3],
                ('v2f', vertex_data), ('t2f', texture_data), ('c4B', [255] * 64))
            glPopAttrib()
