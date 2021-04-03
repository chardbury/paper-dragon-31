'''applib.scenes.level -- level scene

'''

import math
import pprint
import random

import applib
import pyglet

from applib import app
from applib.engine import animation
from applib.engine import sound

from pyglet.gl import *


def make_dialogue_interface(self):

    self.dialogue_overlay = self.interface.add(
        width = 1.0,
        height = 1.0,
        align_x = 0.5,
        align_y = 0.5,
        background_color = (255, 255, 255, 150),
        visible = False,
    )

    self.character_left = self.dialogue_overlay.add(
        width = 0.25,
        height = 0.5,
        align_x = 0.15,
        align_y = 0.39,
        anchor_y = 0.0,
        image_flip_x = True,
    )

    self.name_left = self.character_left.add(
        padding = -0.05,
        width = 1.0,
        height = 0.15,
        align_x = 0.5,
        align_y = 1.02,
        anchor_y = 0.0,
        text = '',
        text_color = (0, 0, 0, 255),
        text_bold = True,
        text_wrap = False,
        font_size = 0.04,
        visible = False,
        background_color = (244, 236, 186, 255),
        frame_texture = pyglet.resource.texture('interface/border_plain.png'),
        frame_width = 0.15,
    )

    self.character_right = self.dialogue_overlay.add(
        width = 0.25,
        height = 0.5,
        align_x = 0.85,
        align_y = 0.39,
        anchor_y = 0.0,
    )

    self.name_right = self.character_right.add(
        padding = -0.05,
        width = 1.0,
        height = 0.15,
        align_x = 0.5,
        align_y = 1.02,
        anchor_y = 0.0,
        text = '',
        text_color = (0, 0, 0, 255),
        text_bold = True,
        text_wrap = False,
        font_size = 0.04,
        visible = False,
        background_color = (244, 236, 186, 255),
        frame_texture = pyglet.resource.texture('interface/border_plain.png'),
        frame_width = 0.15,
    )

    self.message_container = self.dialogue_overlay.add(
        width = 0.8,
        height = 0.15,
        padding = -0.02,
        align_x = 0.5,
        align_y = 0.31,
        anchor_y = 1.0,
        background_color = (244, 236, 186, 255),
        frame_texture = pyglet.resource.texture('interface/border.png'),
        frame_width = 0.15,
    )

    self.message_area = self.message_container.add(
        align_y = 1.05,
        align_x = 0.0,
        anchor_y = 1.0,
        text_color = (0, 0, 0, 255),
        font_size = 0.04,
    )



class VictoryScene(object):

    def __init__(self, level=None):
        
        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background_color = (255, 255, 255, 0),
        )

        self.bg_textures = [
            pyglet.resource.texture('scenery/background_village.png'),
            pyglet.resource.texture('scenery/counter.png'),
        ]
        
        make_dialogue_interface(self)
        self.dialogue_overlay.visible = True

        self.scene_fade = 1.0
        animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 0.0, 1.0),
        ).start()
        app.music.switch(pyglet.resource.media('music/badoink_digitaldonut.mp3'))

        app.window.set_mouse_cursor(None)
        self.start_scene('credits')

    def start_scene(self, name, slowly=None):
        if name is not None:
            self.name_left.text_update(None)
            self.name_right.text_update(None)
            self.name_left.visible = False
            self.name_right.visible = False
            self.character_left.image_texture = None
            self.character_right.image_texture = None
            self.message_container.visible = False
            self.message_area.text_update(None)
            self.scene_lines = pyglet.resource.file(f'scenes/{name}.txt', 'r').readlines()
            self.dialogue_overlay.visible = True
            self.advance_scene()

    def advance_scene(self):
        while len(self.scene_lines) > 0:
            line = self.scene_lines.pop(0).strip()
            if len(line) == 0:
                continue
            command, value = map(str.strip, line.split(':', 1))

            if command == 'set_left_image':
                if len(value) > 0:
                    self.character_left.image_texture = pyglet.resource.texture(f'characters/{value}.png')
                else:
                    self.character_left.image_texture = None
            if command == 'set_right_image':
                if len(value) > 0:
                    self.character_right.image_texture = pyglet.resource.texture(f'characters/{value}.png')
                else:
                    self.character_right.image_texture = None

            if command == 'set_left_name':
                self.name_left.text_update(value or None)
            if command == 'set_right_name':
                self.name_right.text_update(value or None)

            if command == 'say_left':
                self.message_container.visible = True
                self.message_area.text_update(value)
                self.name_left.visible = bool(self.name_left.text)
                self.name_right.visible = False
                self.character_left.image_color = (255, 255, 255, 255)
                self.character_right.image_color = (75, 75, 75, 255)
                break
            if command == 'say_right':
                self.message_container.visible = True
                self.message_area.text_update(value)
                self.name_right.visible = bool(self.name_right.text)
                self.name_left.visible = False
                self.character_right.image_color = (255, 255, 255, 255)
                self.character_left.image_color = (75, 75, 75, 255)
                break
            if command == 'say_both':
                self.message_container.visible = True
                self.message_area.text_update(value)
                self.name_left.visible = bool(self.name_left.text)
                self.name_right.visible = bool(self.name_right.text)
                self.character_right.image_color = (255, 255, 255, 255)
                self.character_right.image_color = (255, 255, 255, 255)
                break

            if command == 'end_game':
                frate = app.music.volume / 4.0
                app.music.switch(None, frate)
                animation.QueuedAnimation(
                    animation.AttributeAnimation(self, 'scene_fade', 1.0, 4.0),
                    animation.WaitAnimation(0.5, pyglet.app.exit),
                ).start()
                break

    def on_mouse_release(self, x, y, button, modifiers):
        self.advance_scene()

    def on_draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        app.window.clear()
        x, y = map(int, self.interface.get_offset())
        w, h = map(int, self.interface.get_content_size())
        glEnable(GL_SCISSOR_TEST)
        glScissor(x, y, w, h)
        for tex in self.bg_textures:
            glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
            glEnable(tex.target)
            glBindTexture(tex.target, tex.id)
            pyglet.graphics.draw(4, GL_QUADS,
                ('v2f', [x, y, x+w, y, x+w, y+h, x, y+h]),
                ('t3f', tex.tex_coords),
                ('c4B', [255] * 16),
            )
            glPopAttrib()
        self.interface.draw()
        if self.scene_fade > 0.0:
            w, h = app.window.get_size()
            alpha = max(0, min(255, int(256*self.scene_fade)))
            color = [0, 0, 0, alpha]
            pyglet.graphics.draw(4, GL_QUADS, ('v2f', [0,0,w,0,w,h,0,h]), ('c4B', color*4))
        glDisable(GL_SCISSOR_TEST)
