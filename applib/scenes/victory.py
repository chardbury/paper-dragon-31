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

VICTORY_TEXT = [
    'You did it! Now you will be able to make the world\'s largest apple crumble!',
    'This game was an entry in PyWeek 31.',
    'It was developed by Joey Anrep, David Birch, Carrie de Lacy, Chris de Lacy, Paul Scrivens, and Richard Thomas',
    'Thank you for playing!',
]


class VictoryScene(object):

    def __init__(self, level=None):

        self.messages = list(VICTORY_TEXT)
        
        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background_color = (100, 100, 220, 255),
        )

        self.dialogue_overlay = self.interface.add(
            width = 1.0,
            height = 1.0,
            align_x = 0.5,
            align_y = 0.5,
            background_color = (255, 255, 255, 200),
        )

        self.character_left = self.dialogue_overlay.add(
            width = 0.25,
            height = 0.5,
            align_x = 0.15,
            align_y = 0.38,
            anchor_y = 0.0,
            visible = False,
        )

        self.name_left = self.character_left.add(
            padding = -0.05,
            width = 1.0,
            height = 0.15,
            align_x = 0.0,
            align_y = 0.14,
            text = '',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            text_wrap = False,
            font_size = 0.03,
            visible = False,
            background_color = (230, 230, 230, 255),
            frame_texture = pyglet.resource.texture('interface/border_plain.png'),
            frame_width = 0.15,
        )

        self.character_right = self.dialogue_overlay.add(
            width = 0.25,
            height = 0.5,
            align_x = 0.85,
            align_y = 0.38,
            anchor_y = 0.0,
            visible = False,
        )

        self.name_right = self.character_right.add(
            padding = -0.05,
            width = 1.0,
            height = 0.15,
            align_x = 1.0,
            align_y = 0.14,
            text = '',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            text_wrap = False,
            font_size = 0.03,
            visible = False,
            background_color = (230, 230, 230, 255),
            frame_texture = pyglet.resource.texture('interface/border_plain.png'),
            frame_width = 0.15,
        )

        self.message_container = self.interface.add(
            width = 0.8,
            height = 0.2,
            padding = 0.02,
            align_x = 0.5,
            align_y = 0.3,
            anchor_y = 1.0,
            background_color = (230, 230, 230, 255),
            frame_texture = pyglet.resource.texture('interface/border.png'),
            frame_width = 0.15,
        )

        self.message_area = self.message_container.add(
            align_y = 1.0,
            align_x = 0.0,
            text_color = (0, 0, 0, 255),
            font_size = 0.03,
            text = self.messages.pop(0),
        )

        self.scene_fade = 1.0
        animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 0.0, 1.0),
        ).start()
        app.music.switch(pyglet.resource.media('music/badoink_digitaldonut.mp3'))

        app.window.set_mouse_cursor(None)

    def on_mouse_release(self, x, y, button, modifiers):
        if self.messages:
            self.message_area.text_update(self.messages.pop(0))
        else:
            animation.QueuedAnimation(
                animation.AttributeAnimation(self, 'scene_fade', 1.0, 1.0),
                animation.WaitAnimation(0.1, pyglet.app.exit),
            ).start()

    def on_draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        app.window.clear()
        x, y = map(int, self.interface.get_offset())
        w, h = map(int, self.interface.get_content_size())
        glEnable(GL_SCISSOR_TEST)
        glScissor(x, y, w, h)
        self.interface.draw()
        if self.scene_fade > 0.0:
            w, h = app.window.get_size()
            alpha = max(0, min(255, int(256*self.scene_fade)))
            color = [0, 0, 0, alpha]
            pyglet.graphics.draw(4, GL_QUADS, ('v2f', [0,0,w,0,w,h,0,h]), ('c4B', color*4))
        glDisable(GL_SCISSOR_TEST)
