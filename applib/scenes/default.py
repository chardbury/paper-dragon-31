'''applib.scenes.default -- default scene

'''

import random

import applib
import pyglet

from applib import app
from applib.engine import animation
from applib.engine import music


class DefaultScene(object):

    def __init__(self):

        self.logo_image = pyglet.resource.image('logos/paper_dragon_large.png')
        self.logo_image.anchor_x = self.logo_image.width // 2
        self.logo_image.anchor_y = self.logo_image.height // 2
        self.logo_sprite = pyglet.sprite.Sprite(self.logo_image)
        self.logo_sprite.x = app.window.width // 2
        self.logo_sprite.y = app.window.height // 2
        self.logo_sprite.scale = (app.window.width // 2) / self.logo_image.width
        self.logo_sprite.opacity = 0.0

        animation.QueuedAnimation(
            animation.WaitAnimation(1.0),
            animation.AttributeAnimation(self.logo_sprite, 'opacity', 255.0, 100.0),
            animation.WaitAnimation(2.0),
            animation.AttributeAnimation(self.logo_sprite, 'opacity', 0.0, 100.0),
            animation.WaitAnimation(1.0),
        ).start()

        pyglet.resource.media(f'sounds/rawr{random.randint(1, 3)}.mp3').play()

        background_music = pyglet.resource.media('music/ketsa_love.mp3')
        app.music.switch(background_music)

        self.loading_label = pyglet.text.Label(
            text = 'Loading...',
            font_name = 'Lato',
            font_size = 0.08 * app.window.height,
            bold = True,
            color = (255, 255, 255, 255),
            x = app.window.width // 2,
            y = app.window.height // 40,
            anchor_x = 'center',
            anchor_y = 'bottom',
        )

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.MINUS:
            new_volume = max(0.0, app.settings.volume - 0.05)
            app.settings.save_settings(volume=new_volume)
        if symbol == pyglet.window.key.EQUAL:
            new_volume = min(1.0, app.settings.volume + 0.05)
            app.settings.save_settings(volume=new_volume)

    def on_draw(self):
        app.window.clear()
        self.logo_sprite.draw()
        self.loading_label.draw()
