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
            background = (200, 200, 200, 255),
        )

        p1 = self.interface.add(Panel,
            width = 0.8,
            height = 0.6,
            background = (255, 0, 0, 255),
        )
        
        p2 = p1.add(Panel,
            width = 0.5,
            height = 0.2,
            background = (0, 255, 0, 255),
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
