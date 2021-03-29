'''applib.scenes.default -- default scene

'''

import random

import applib
import pyglet

from applib import app
from applib.engine import animation
from applib.engine import music
from applib.engine import sound


class MenuScene(object):

    def __init__(self):

        # self.logo_image = pyglet.resource.image('logos/paper_dragon_large.png')
        # self.logo_image.anchor_x = self.logo_image.width // 2
        # self.logo_image.anchor_y = self.logo_image.height // 2
        # self.logo_sprite = pyglet.sprite.Sprite(self.logo_image)
        # self.logo_sprite.x = app.window.width // 2
        # self.logo_sprite.y = app.window.height // 2
        # self.logo_sprite.scale = (app.window.width // 2) / self.logo_image.width
        # self.logo_sprite.opacity = 0.0

        # self.logo_animation = animation.QueuedAnimation(
        #     animation.WaitAnimation(1.0, sound.rawr),
        #     animation.AttributeAnimation(self.logo_sprite, 'opacity', 255.0, 100.0, 'symmetric'),
        #     animation.WaitAnimation(2.0),
        #     animation.AttributeAnimation(self.logo_sprite, 'opacity', 0.0, 100.0),
        #     animation.WaitAnimation(1.0),
        # ).start()

        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background = (50, 50, 50, 255),
        )

        self.title = self.interface.add(
            height = 0.2,
            align_y = 1.0,
            background = (50, 200, 50, 255),
            text = 'Cop, Cake, Caper!'
        )

        self.menu = self.interface.add(
            width = 0.5,
            height = 0.5,
            align_y = 0.2,
            background = (200, 50, 50, 255),
        )

    def on_draw(self):
        app.window.clear()
        self.interface.draw()
        # self.logo_sprite.draw()
