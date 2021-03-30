'''applib.scenes.level -- level scene

'''

import math
import random

import applib
import pyglet

from applib import app
from applib.constants import COUNTER_EDGE_ADJUSTMENT
from applib.constants import CURSOR_SCALE
from applib.constants import CUSTOMER_BOUNCE_DISTANCE
from applib.constants import CUSTOMER_BOUNCE_SPEED
from applib.constants import CUSTOMER_POSITIONS
from applib.constants import CUSTOMER_SCALE
from applib.constants import CUSTOMER_WALK_SPEED
from applib.constants import DEBUG
from applib.constants import DEVICE_SCALE
from applib.constants import ITEM_SCALE
from applib.constants import SCENERY_SCALE
from applib.engine import animation
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
        self.level.push_handlers(self)

        # Create the root interface panel.
        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background = (100, 100, 220, 255),
        )

        self.load_level_sprites()

    ## Model
    ## -----

    def create_test_level(self):
        level = applib.model.level.TestLevel()
        applib.model.scenery.Counter(level)
        return level

    def load_level_sprites(self):
        self.sprites_by_entity = {}
        self.entities_by_sprite = {}
        self.persisting_sprites = {}
        #self.create_sprite('scenery/counter.png', 0.5, 0.0, -0.25)
        for entity in self.level.entities:
            self.update_sprite(entity)
        for device in self.level.devices:
            sprite = self.update_sprite(device)

    _entity_properties = [
        (applib.model.level.Customer, CUSTOMER_SCALE, -1),
        (applib.model.device.Device, DEVICE_SCALE, 1),
        (applib.model.item.Item, ITEM_SCALE, 2),
        (applib.model.scenery.Scenery, SCENERY_SCALE, 0),
    ]

    def update_sprite(self, entity):
        if entity.sprite is not None:
            sprite = entity.sprite
            texture = sprite._texture

            view_width, view_height = self.interface.get_content_size()
            move_x, move_y = self.compute_position(entity)

            # Update the sprite indexes.
            self.sprites_by_entity[entity] = sprite
            self.entities_by_sprite[sprite] = entity

            # Ensure the sprite is in the interface
            if sprite not in self.interface.sprites:
                self.interface.sprites.append(sprite)

                # Cache the texture data for alpha hit testing.
                texture_data = texture.get_image_data().get_data()
                self._texture_data[texture] = texture_data
            
                # Get the proprties used to configure the sprite.
                for entity_class, relative_height, sprite_layer in self._entity_properties:
                    if isinstance(entity, entity_class):
                        break

                # Configure the sprite and its texture.
                texture.anchor_x = texture.width // 2
                texture.anchor_y = texture.height // 2
                sprite.scale = (relative_height * view_height) / texture.height
                if sprite_layer is not None:
                    sprite.layer = sprite_layer

                # Position the sprite.
                if move_x is not None:
                    sprite.x = view_width / 2 + move_x * view_height
                if move_y is not None:
                    sprite.y = view_height / 2 + move_y * view_height

                # Start the necessary animations.
                if self._is_interactable(entity):
                    sprite.animate_zoom()

    def compute_position(self, entity):
        move_x, move_y = 0.0, 0.0

        # Position customers based on how many there are.
        if isinstance(entity, applib.model.level.Customer):
            customer_count = len(self.level.customers)
            customer_index = self.level.customers.index(entity)
            aspect = entity.sprite._texture.width / entity.sprite._texture.height
            move_x = 0.0 # CUSTOMER_POSITIONS[customer_count][customer_index]
            move_y = CUSTOMER_SCALE * (aspect - 0.5) + COUNTER_EDGE_ADJUSTMENT

        if isinstance(entity, applib.model.device.Device):
            move_x, move_y = self.level.device_locations[entity]

        return move_x, move_y

    def on_customer_arrives(self, customer):
        view_width, view_height = self.interface.get_content_size()

        # Create and animate the sprite.
        self.update_sprite(customer)
        customer.sprite.queue_animation(
            applib.engine.sprite.WalkAnimation(
                sprite = customer.sprite,
                walk_speed = CUSTOMER_WALK_SPEED * view_height,
                bounce_distance = CUSTOMER_BOUNCE_DISTANCE * view_height,
                bounce_speed = CUSTOMER_BOUNCE_SPEED,
            )
        )

        # Have all the customers reposition.
        customer_count = len(self.level.customers)
        for index, other_customer in enumerate(self.level.customers):
            move_x = CUSTOMER_POSITIONS[customer_count][index]
            other_customer.sprite.walk_target = move_x * view_height
            if other_customer is customer:
                direction = 1 if (random.random() * view_width < move_x * view_height) else -1
                customer.sprite.animation_offset_x = direction * view_width / 2

    def on_customer_leaves(self, customer):
        view_width, view_height = self.interface.get_content_size()

        # Have the leaving customer walk off.
        direction = 1 if (random.random() * view_width < customer.sprite.x) else -1
        customer.sprite.walk_target = direction * view_width
        self.persisting_sprites[customer.sprite] = (lambda:
            abs(customer.sprite.animation_offset_x) > view_width / 2)

        # Have the remaining customers reposition.
        customer_count = len(self.level.customers)
        for index, other_customer in enumerate(self.level.customers):
            move_x = CUSTOMER_POSITIONS[customer_count][index]
            other_customer.sprite.walk_target = move_x * view_height

    def on_tick(self):
        self.level.tick()

        # Update the sprites for all entities in the level.
        for entity in self.level.entities:
            self.update_sprite(entity)

        # Depersist any persisting sprites whose check passes.
        for sprite, persist_check in list(self.persisting_sprites.items()):
            if persist_check():
                del self.persisting_sprites[sprite]
        
        # Remove sprites for missing entities from the scene.
        found_sprites = set(entity.sprite for entity in self.level.entities) | set(self.persisting_sprites)
        for sprite in self.interface.sprites:
            if sprite not in found_sprites:
                sprite.stop_animation()
                self.interface.sprites.remove(sprite)

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

    def _is_interactable(self, entity):
        return hasattr(entity, 'interact')

    def _change_sprite_focus(self, new_sprite, old_sprite):
        if new_sprite is not None:
            target = self.entities_by_sprite[new_sprite]
            if self._is_interactable(target):
                new_sprite._target_zoom = 1.1
        if old_sprite is not None:
            old_sprite._target_zoom = 1.0

    def _get_sprite_at(self, target_x, target_y):
        '''Return the sprite at the specified window coordinates.

        '''
        offset_x, offset_y = self.interface.get_offset()
        for sprite in reversed(self.interface.sprites):
            texture = sprite._texture
            # 1. Get the position of the target relative to the sprite in the window frame.
            sprite_x = target_x - (sprite.x + sprite.animation_offset_x + offset_x)
            sprite_y = target_y - (sprite.y + sprite.animation_offset_y + offset_y)
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
                    return sprite
    
    def _update_mouse_position(self, mouse_x, mouse_y):
        '''Update the mouse position and record the targeted sprite.

        '''
        self._mouse_x, self._mouse_y = mouse_x, mouse_y
        new_target_sprite = self._get_sprite_at(mouse_x, mouse_y)
        if new_target_sprite != self._target_sprite:
            self._change_sprite_focus(new_target_sprite, self._target_sprite)
            self._target_sprite = new_target_sprite

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
                target = self.entities_by_sprite[self._clicked_sprite]
                if self._is_interactable(target):
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
            view_width, view_height = self.interface.get_content_size()
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
