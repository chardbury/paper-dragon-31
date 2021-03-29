'''applib.scenes.level -- level scene

'''

import math

import applib
import pyglet

from applib import app
from applib.constants import CURSOR_SCALE
from applib.constants import CUSTOMER_SCALE
from applib.constants import DEVICE_SCALE
from applib.constants import ITEM_SCALE
from applib.engine import sound

from pyglet.gl import *


class ScaledImageMouseCursor(pyglet.window.ImageMouseCursor):

    def __init__(self, image, height, hot_x=0.0, hot_y=0.0):
        super().__init__(image, hot_x, hot_y)
        self.height = height
    
    def draw(self, x, y):

        # Compute the coordinates of the cursor box.
        scale = self.height / self.texture.height
        x1 = x - (self.hot_x + self.texture.anchor_x) * scale
        y1 = y - (self.hot_y + self.texture.anchor_y) * scale
        x2 = x1 + self.texture.width * scale
        y2 = y1 + self.texture.height * scale

        # Render the texture in the cursor box.
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)
        pyglet.graphics.draw_indexed(4, GL_TRIANGLES,
            [0, 1, 2, 0, 2, 3],
            ('v2f', [x1, y1, x2, y1, x2, y2, x1, y2]),
            ('t3f', self.texture.tex_coords),
            ('c4B', [255] * 16),
        )
        glPopAttrib()


class LevelScene(object):
    '''Class comprising the main interface to `applib.model.level.Level`.

    '''

    def __init__(self, level=None):
        '''Create a `LevelScene` object.

        '''

        # Ensure we have an appropriate level.
        self.level = level or self.create_test_level()

        # Create the root interface panel.
        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background = (100, 100, 220, 255),
        )

        self.load_level_sprites()

    ## Model
    ## -----

    def create_test_level(self):
        return applib.model.level.TestLevel()

    def load_level_sprites(self):
        self.level_sprite_map = {}
        self.create_sprite('scenery/counter.png', 0.5, 0.0, -0.25)
        for device in self.level.devices:
            relative_x, relative_y = self.level.device_locations[device]
            sprite = self.create_sprite(device, DEVICE_SCALE, relative_x, relative_y)

    def create_sprite(self, target,
        relative_height=0.1,
        relative_x=0.0,
        relative_y=0.0,
        layer=10,
        ):

        if isinstance(target, applib.model.entity.Entity):
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
        self.level_sprite_map[sprite] = target
        self.interface.sprites.append(sprite)
        self._texture_data[texture] = texture.get_image_data().get_data()
        return sprite

    def on_tick(self):
        self.level.tick()

        # Check for old sprites to remove.
        reverse_map = {}
        for sprite, entity in list(self.level_sprite_map.items()):
            if isinstance(entity, applib.model.level.Customer):
                if entity not in self.level.customers:
                    del self.level_sprite_map[sprite]
                    self.interface.sprites.remove(sprite)    
                    continue
            reverse_map[entity] = sprite

        # Check for new sprites to add.
        for index, customer in enumerate(self.level.customers):
            customer_positions = [[], [0.0], [-0.3, 0.3], [-0.5, 0.0, 0.5], [-0.6, -0.2, 0.2, 0.6]]
            relative_x = customer_positions[len(self.level.customers)][index]
            if customer not in reverse_map:
                self.create_sprite(customer, CUSTOMER_SCALE, relative_x, 0.0, 9)
            else:
                view_width, view_height = self.interface.get_size()
                reverse_map[customer].x = relative_x * view_height + view_width / 2


    ## Clicking
    ## --------

    #: The most recent coordinates of the mouse cursor.
    _mouse_x, _mouse_y = 0, 0

    #: The sprite that is currently under the mouse cursor.
    _target_sprite = None

    #: The sprite that has been clicked on, but not yet released.
    _clicked_sprite = None

    #: The cached texture data used in alpha based hit testing.
    _texture_data = {}

    def _get_sprite_at(self, target_x, target_y):
        '''Return the sprite at the specified window coordinates.

        '''
        offset_x, offset_y = self.interface.get_offset()
        for sprite in self.interface.sprites: sprite.color = (255, 255, 255)
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
                alpha_index = (texture_y * texture.width + texture_x) * 4 + 3
                if self._texture_data[texture][alpha_index] > 0:
                    sprite.color = (0, 0, 0)
                    return sprite
    
    def _update_mouse_position(self, mouse_x, mouse_y):
        '''Update the mouse position and record the targeted sprite.

        '''
        self._mouse_x, self._mouse_y = mouse_x, mouse_y
        self._target_sprite = self._get_sprite_at(mouse_x, mouse_y)

    def on_mouse_enter(self, x, y):
        self._update_mouse_position(x, y)

    def on_mouse_leave(self, x, y):
        self._update_mouse_position(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        self._update_mouse_position(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self._update_mouse_position(x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self._update_mouse_position(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        self._update_mouse_position(x, y)
        self._clicked_sprite = self._target_sprite

    def on_mouse_release(self, x, y, button, modifiers):
        self._update_mouse_position(x, y)
        if self._clicked_sprite is not None:
            if self._target_sprite is self._clicked_sprite:
                # Zhu Li, do the thing!
                target = self.level_sprite_map[self._clicked_sprite]
                self.level.interact(target)
                sound.pop()
            self._clicked_sprite = None

    ## Rendering
    ## ---------

    _cursor_cache = {}

    def set_cursor(self, image):
        '''Use the texture from the given object as the mouse cursor.

        '''
        # Acquire the texture from the input object.
        if isinstance(image, pyglet.sprite.Sprite):
            image = image._texture
        if isinstance(image, pyglet.image.AbstractImage):
            cursor_texture = image.get_texture()
        else:
            app.window.set_mouse_cursor(None)
            return

        # Create and cache the cursor object.
        if cursor_texture not in self._cursor_cache:
            view_width, view_height = self.interface.get_size()
            cursor_height = CURSOR_SCALE * view_height
            cursor_x = cursor_texture.width / 2
            cursor_y = cursor_texture.width / 2
            cursor = ScaledImageMouseCursor(cursor_texture, cursor_height, cursor_x, cursor_y)
            self._cursor_cache[cursor_texture] = cursor
        else:
            cursor = self._cursor_cache[cursor_texture]

        # Set the cursor on the window.
        app.window.set_mouse_cursor(cursor)

    def on_draw(self):

        # Clear the buffers.
        app.window.clear()

        if self.level.held_item:
            self.set_cursor(self.level.held_item.sprite)
        else:
            app.window.set_mouse_cursor(None)

        # Order the sprites for rendering.
        layer_key = (lambda sprite: sprite.layer)
        self.interface.sprites.sort(key=layer_key)

        # Render the interface.
        self.interface.draw()
