'''applib.scenes.level -- level scene

'''

import applib
import pyglet

from applib import app
from applib.engine import panel
from applib.constants import ITEM_SCALE
from applib.constants import DEVICE_SCALE


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

        #self.set_cursor('cursors/default.png')

        self.interface = panel.Panel(
            aspect = (16, 9),
            background = (100, 100, 220, 255),
        )

        self.sprite_index = {}

        self.create_sprite('scenery/counter.png', 0.5, 0.0, -0.25)

        for device in self.level.devices:
            relative_x, relative_y = self.level.device_locations[device]
            sprite = self.create_sprite(device, DEVICE_SCALE, relative_x, relative_y)

    def create_sprite(self, target,
        relative_height=0.1,
        relative_x=0.0,
        relative_y=0.0,
        layer=0,
        ):

        if isinstance(target, applib.model.item.Item):
            texture = target.image
        elif isinstance(target, applib.model.device.Device):
            texture = target.texture
        elif isinstance(target, str):
            texture = pyglet.resource.texture(target)
        else:
            return

        view_width, view_height = self.interface.get_size()
        texture.anchor_x = texture.width // 2
        texture.anchor_y = texture.height // 2
        sprite = pyglet.sprite.Sprite(texture)
        sprite.scale = (relative_height * view_height) / texture.height
        sprite.x = relative_x * view_height + view_width / 2
        sprite.y = relative_y * view_height + view_height / 2
        sprite.layer = layer
        self.sprite_index[target] = sprite
        self.interface.sprites.append(sprite)
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

        # Clear the buffers.
        app.window.clear()

        # Order the sprites for rendering.
        layer_key = (lambda sprite: sprite.layer)
        self.interface.sprites.sort(key=layer_key)

        # Render the interface.
        self.interface.draw()
