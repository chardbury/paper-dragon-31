'''applib.scenes.default -- default scene

'''

import random

import applib
import pyglet

from applib import app
from applib.engine import animation
from applib.engine import music
from applib.engine import sound

from pyglet.gl import *


class MenuScene(object):

    def __init__(self):

        self.overlay = pyglet.resource.texture('overlays/burlap_256.png')

        self.logo_image = pyglet.resource.image('logos/paper_dragon_large.png')
        self.logo_image.anchor_x = self.logo_image.width // 2
        self.logo_image.anchor_y = self.logo_image.height // 2
        self.logo_sprite = pyglet.sprite.Sprite(self.logo_image)
        self.logo_sprite.x = app.window.width // 2
        self.logo_sprite.y = app.window.height // 2
        self.logo_sprite.scale = (app.window.width // 2) / self.logo_image.width
        self.logo_sprite.opacity = 0.0

        self.logo_animation = animation.QueuedAnimation(
            animation.WaitAnimation(1.0, self.do_rawr),
            animation.AttributeAnimation(self.logo_sprite, 'opacity', 255.0, 2.0, 'symmetric'),
            animation.WaitAnimation(2.0),
            animation.AttributeAnimation(self.logo_sprite, 'opacity', 0.0, 2.0),
            animation.WaitAnimation(1.0, self.end_logo),
        ).start()

        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background_color = (255, 255, 255, 255),
            visible = False,
        )

        self.title_image = self.interface.add(
            width = 1.0,
            height = 0.84,
            align_y = 0.58,
            anchor_y = 0.5,
            image_texture = pyglet.resource.texture('scenery/background_village.jpg')
        )

        self.play_button = self.interface.add(
            align_x = 0.17,
            align_y = 0.08,
            anchor_x = 0.5,
            anchor_y = 0.5,
            height = 0.1,
            text = 'Play',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            font_size = 0.06,
        )

        self.continue_button = self.interface.add(
            align_x = 0.5,
            align_y = 0.08,
            anchor_x = 0.5,
            anchor_y = 0.5,
            height = 0.1,
            text = 'Unused',
            text_bold = True,
            text_color = (0, 0, 0, 255),
            font_size = 0.06,
            visible = False
        )

        self.quit_button = self.interface.add(
            align_x = 0.83,
            align_y = 0.08,
            anchor_x = 0.5,
            anchor_y = 0.5,
            height = 0.1,
            text = 'Quit',
            text_bold = True,
            text_color = (0, 0, 0, 255),
            font_size = 0.06,
        )

    rawr_player = None

    def do_rawr(self):
        if self.rawr_player:
            self.rawr_player.pause()
        self.rawr_player = sound.rawr()

    def end_logo(self):
        if self.rawr_player:
            self.rawr_player.pause()
        self.logo_animation.stop()
        self.logo_sprite.visible = False
        self.interface.visible = True

    _hover_button = None

    _press_button = None

    def _update_mouse_position(self, x, y):
        new_hover_button = \
            'play' if self.play_button.contains(x, y) else \
            'quit' if self.quit_button.contains(x, y) else \
            None

        if (new_hover_button is not None) and (new_hover_button != self._hover_button):
            sound.click()
        self._hover_button = new_hover_button

        self.play_button.text_color = (80, 80, 80, 255) if self._hover_button == 'play' else (0, 0, 0, 255)
        self.quit_button.text_color = (80, 80, 80, 255) if self._hover_button == 'quit' else (0, 0, 0, 255)

    def on_mouse_enter(self, x, y):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_leave(self, x, y):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.interface.visible:
            self._update_mouse_position(x, y)
            self._press_button = self._hover_button

    def on_mouse_release(self, x, y, button, modifiers):
        if self.interface.visible:
            self._update_mouse_position(x, y)
            if (self._press_button is not None) and (self._hover_button == self._press_button):
                getattr(self, f'do_button_{self._press_button}')()
            self._press_button = None
        else:
            self.end_logo()

    def do_button_play(self):
        app.controller.switch_scene(applib.scenes.level.LevelScene)

    def do_button_quit(self):
        pyglet.app.exit()

    def on_draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        app.window.clear()
        self.interface.draw()
        self.logo_sprite.draw()

        # Render overlay
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(self.overlay.target)
        glBindTexture(self.overlay.target, self.overlay.id)
        glTexParameteri(self.overlay.target, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(self.overlay.target, GL_TEXTURE_WRAP_T, GL_REPEAT)
        x, y = map(int, self.interface.get_offset())
        w, h = map(int, self.interface.get_content_size())
        vertex_data = [x, y, x + w, y, x + w, y + h, x, y + h]
        texture_data = [v / self.overlay.width for v in vertex_data]
        color_data = [255, 255, 255, 255] * 4
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t2f', texture_data), ('c4B', color_data))
        glPopAttrib()
