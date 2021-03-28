'''applib.scenes.level -- level scene

'''

import applib
import pyglet

from applib import app
from applib.engine.panel import Panel


def create_sprite(filename, size):
    image = pyglet.resource.image(filename)
    image.anchor_x = image.width // 2
    image.anchor_y = image.height // 2
    sprite = pyglet.sprite.Sprite(image)
    sprite.scale = size / image.height
    return sprite


class LevelScene(object):

    def __init__(self, level=None):
        self.level = level or applib.model.level.Level()
        self.set_cursor('cursors/default.png')

        self.interface = Panel(
            aspect = (16, 9),
            background = (100, 100, 220, 255),
        )

        self.counter = self.interface.add(Panel,
            align_y = 0.0,
            width = 1.0,
            height = 0.65,
            background = (53, 20, 2, 255),
        )

    def set_cursor(self, filename):
        cursor_image = pyglet.resource.image(filename)
        cursor = pyglet.window.ImageMouseCursor(
            cursor_image,
            cursor_image.width // 2,
            cursor_image.height // 2,
        )
        app.window.set_mouse_cursor(cursor)

    def on_tick(self):
        self.level.tick()

    def on_mouse_release(self, x, y, button, modifiers):
        pass
        #if clicked_on_batter_box:
        #    self.level.pick_up_batter()

    def on_draw(self):
        app.window.clear()
        self.interface.draw()

        #self.cursor_sprite.image = 'batter.png'
