'''applib.scenes.level -- level scene

'''

import applib
import pyglet

from applib import app
from applib.engine import panel
from applib.constants import ITEM_SCALE


def create_sprite(filename, size):
    image = pyglet.resource.image(filename)
    image.anchor_x = image.width // 2
    image.anchor_y = image.height // 2
    sprite = pyglet.sprite.Sprite(image)
    sprite.scale = size / image.height
    return sprite


class LevelScene(object):

    def __init__(self, level=None):
        self.level = level or applib.model.level.TestLevel()

        self.set_cursor('cursors/default.png')

        self.interface = panel.Panel(
            aspect = (16, 9),
            background = (100, 100, 220, 255),
        )

        self.counter = self.interface.add(
            align_y = 0.0,
            width = 1.0,
            height = 0.5,
            background = (53, 20, 2, 255),
            sprites = [],
        )

        self.sprite_index = {}
        for device in self.level.devices:
            location_x, location_y = self.level.device_locations[device]
            sprite = self.create_counter_sprite(device, location_x, location_y)

        # self.create_counter_sprite(applib.model.item.get('batter'))
        # self.create_counter_sprite(applib.model.item.get('doughnut'), 0.4)
        # self.create_counter_sprite(applib.model.item.get('better_doughnut'), 0.8)
        # self.create_counter_sprite(applib.model.item.get('doughnut_cooked'), 1.2)

    def create_counter_sprite(self, target, offset_x=0.0, offset_y=0.0):

        if isinstance(target, applib.model.item.Item):
            target.image.anchor_x = target.image.width // 2
            target.image.anchor_y = target.image.height // 2
            sprite = pyglet.sprite.Sprite(target.image)
            sprite.scale = (app.window.height * ITEM_SCALE) / target.image.height

        elif isinstance(target, applib.model.device.Device):
            target.texture.anchor_x = target.texture.width // 2
            target.texture.anchor_y = target.texture.height // 2
            sprite = pyglet.sprite.Sprite(target.texture)
            sprite.scale = (app.window.height * ITEM_SCALE) / target.texture.height

        else:
            sprite = None

        counter_width, counter_height = self.counter.get_size()
        sprite.x = offset_x * counter_height + counter_width / 2
        sprite.y = offset_y * counter_height + counter_height / 2
        self.sprite_index[target] = sprite
        self.counter.sprites.append(sprite)
        return sprite

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

    def on_draw(self):
        app.window.clear()
        self.interface.draw()
