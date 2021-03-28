'''applib.scenes.level -- level scene

'''

import applib
import pyglet

from applib import app


def create_sprite(filename, size):
    image = pyglet.resource.image(filename)
    image.anchor_x = image.width // 2
    image.anchor_y = image.height // 2
    sprite = pyglet.sprite.Sprite(image)
    sprite.x = app.window.width // 2
    sprite.y = app.window.height // 2
    sprite.scale = size / image.height
    return sprite
    

class LevelScene(object):

    def __init__(self, level=None):
        self.level = level or applib.model.level.Level()
        self.set_cursor('cursors/default.png')


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
        #self.cursor_sprite.image = 'batter.png'
