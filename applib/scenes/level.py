'''applib.scenes.level -- level scene

'''

import math

import applib
import pyglet

from applib import app
from applib.engine import panel
from applib.constants import ITEM_SCALE
from applib.constants import DEVICE_SCALE

from pyglet.gl import *


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

    ## Mouse Events
    ###############
    
    def _update_mouse_position(self, x, y):
        print(self._get_sprite_at(x, y))

    def _get_sprite_at(self, target_x, target_y):
        offset_x, offset_y = self.interface.get_offset()
        for sprite in self.interface.sprites: sprite.color = (255, 255, 255) # FOR TESTING
        for sprite in reversed(self.interface.sprites):
            texture = sprite._texture
            # 1. Get the position of the target relative to the sprite in the window frame.
            sprite_x = target_x - (sprite.x + offset_x)
            sprite_y = target_y - (sprite.y + offset_y)
            # 2. Get the position of the target relative to the sprite in the sprite frame.
            rotation = math.radians(sprite._rotation)
            sin, cos = math.sin(rotation), math.cos(rotation)
            sprite_x = cos * sprite_x - sin * sprite_y
            sprite_y = sin * sprite_x + cos * sprite_y
            # 3. Get the position of the target relative to the texture in the texture frame.
            scale_x = sprite._scale * sprite._scale_x
            scale_y = sprite._scale * sprite._scale_y
            texture_x = int(sprite_x / scale_x + texture.anchor_x)
            texture_y = int(sprite_y / scale_y + texture.anchor_y)
            # 4. Check if the texture is transparent at the computed position.
            if (0 <= texture_x < texture.width) and (0 <= texture_y < texture.height):
                image_data = texture.get_image_data().get_data()
                alpha_index = (texture_y * texture.width + texture_x) * 4 + 3
                if image_data[alpha_index] > 0:
                    sprite.color = (0, 0, 0) # FOR TESTING
                    return sprite


    def on_mouse_enter(self, x, y):
        self._update_mouse_position(x, y)

    def on_mouse_leave(self, x, y):
        self._update_mouse_position(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self._update_mouse_position(x, y)

    def on_mouse_release(self, x, y, button, modifiers):
        self._update_mouse_position(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self._update_mouse_position(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self._update_mouse_position(x, y)

    def on_draw(self):

        # Clear the buffers.
        app.window.clear()

        # Order the sprites for rendering.
        layer_key = (lambda sprite: sprite.layer)
        self.interface.sprites.sort(key=layer_key)

        # Render the interface.
        self.interface.draw()
