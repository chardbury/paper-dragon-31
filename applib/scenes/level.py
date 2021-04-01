'''applib.scenes.level -- level scene

'''

import math
import pprint
import random

import applib
import pyglet

from applib import app
from applib.constants import COUNTER_EDGE_ADJUSTMENT
from applib.constants import CURSOR_SCALE
from applib.constants import CUSTOMER_BOUNCE_DISTANCE
from applib.constants import CUSTOMER_BOUNCE_SPEED
from applib.constants import CUSTOMER_ORDER_POSITIONS
from applib.constants import CUSTOMER_ORDER_HEIGHT
from applib.constants import CUSTOMER_PATIENCE_BAR_HEIGHT
from applib.constants import CUSTOMER_PATIENCE_BAR_MARGIN
from applib.constants import CUSTOMER_PATIENCE_BAR_VERTICAL_OFFSET
from applib.constants import CUSTOMER_POSITIONS
from applib.constants import CUSTOMER_SCALE
from applib.constants import CUSTOMER_WALK_SPEED
from applib.constants import DEBUG
from applib.constants import DEVICE_SCALE
from applib.constants import ITEM_SCALE
from applib.constants import PROGRESS_BAR_HEIGHT
from applib.constants import PROGRESS_BAR_MARGIN
from applib.constants import PROGRESS_BAR_WIDTH
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
        x1 = x - self.hot_x * scale
        y1 = y - self.hot_y * scale
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
            background_color = (100, 100, 220, 255),
        )

        self.load_level_sprites()

        self.load_dialogue_overlay()

    ## Model
    ## -----

    def create_test_level(self):
        level = applib.model.level.TestLevel()
        applib.model.scenery.Counter(level)
        level.background_scenery(level)
        return level

    def load_level_sprites(self):
        self.sprites_by_entity = {}
        self.entities_by_sprite = {}
        self.persisting_sprites = {}
        for entity in self.level.entities:
            self.update_sprite(entity)
        for device in self.level.devices:
            sprite = self.update_sprite(device)

    _entity_properties = [
        (applib.model.level.Customer, CUSTOMER_SCALE, -1),
        (applib.model.device.Device, DEVICE_SCALE, 1),
        (applib.model.item.Item, ITEM_SCALE, 2),
        (applib.model.scenery.Scenery, SCENERY_SCALE, None),
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
                sprite._can_click_through = isinstance(entity, applib.model.item.Item)

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
                elif hasattr(entity, 'get_layer'):
                    sprite.layer = entity.get_layer()

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
            other_customer.sprite._target_offset_x = move_x * view_height
            if other_customer is customer:
                direction = 1 if (random.random() * view_width < move_x * view_height) else -1
                customer.sprite.animation_offset_x = direction * view_width / 2

    def on_customer_leaves(self, customer):
        view_width, view_height = self.interface.get_content_size()

        # Have the leaving customer walk off.
        direction = 1 if (random.random() * view_width < customer.sprite.x) else -1
        customer.sprite._target_offset_x = direction * view_width
        self.persisting_sprites[customer.sprite] = (lambda:
            abs(customer.sprite.animation_offset_x) > view_width / 2)

        # Have the remaining customers reposition.
        customer_count = len(self.level.customers)
        for index, other_customer in enumerate(self.level.customers):
            move_x = CUSTOMER_POSITIONS[customer_count][index]
            if other_customer is not customer:
                other_customer.sprite._target_offset_x = move_x * view_height

    def on_tick(self):

        if self.dialogue_overlay.visible:
            # Do dialogue things here.
            return pyglet.event.EVENT_HANDLED

        view_width, view_height = self.interface.get_content_size()

        # Update the level first.
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
        for sprite in list(self.interface.sprites):
            if sprite not in found_sprites:
                sprite.stop_animation()
                self.interface.sprites.remove(sprite)
                entity = self.entities_by_sprite[sprite]
                del self.entities_by_sprite[sprite]
                del self.sprites_by_entity[entity]

        # Update remaining sprites.
        processed_items = []
        for sprite, entity in self.entities_by_sprite.items():
            
            # Move order sprites to follow their customer.
            if isinstance(entity, applib.model.level.Customer):
                entity.sprite.overlay_function = self.draw_customer_overlay
                order_count = len(entity.order.items)
                for index, item in enumerate(entity.order.items):
                    processed_items.append(item)
                    order_arc_angle = CUSTOMER_ORDER_POSITIONS[order_count][index]
                    order_arc_radius = CUSTOMER_ORDER_HEIGHT * view_height + sprite.height / 2
                    relative_position_x = order_arc_radius * math.sin(math.radians(order_arc_angle))
                    relative_position_y = order_arc_radius * math.cos(math.radians(order_arc_angle))
                    customer_center = sprite.x + sprite.animation_offset_x
                    position_x = customer_center + relative_position_x
                    position_y = sprite.y + relative_position_y
                    item.sprite.layer = sprite.layer + 0.5
                    item.sprite.update(
                        x = position_x,
                        y = position_y,
                        rotation = order_arc_angle,
                    )
                    item.sprite.set_background_sprite(pyglet.resource.texture('interface/speech_bubble.png'))
                    item.sprite.update_background_sprite()
            
            # Move current item sprites to their device.
            if isinstance(entity, applib.model.device.Device):
                if entity.current_item is not None:
                    processed_items.append(entity.current_item)
                    entity.current_item.sprite.layer = sprite.layer + 0.5
                    entity.current_item.sprite.update(
                        x = sprite.x,
                        y = sprite.y,
                    )

        # Postprocessing for items.
        for sprite, entity in self.entities_by_sprite.items():
            if isinstance(entity, applib.model.item.Item):
                sprite.visible = True
                if entity not in processed_items:
                    if entity is self.level.held_item:
                        sprite.visible = False
                    elif DEBUG:
                        self.level.debug_print()

    ## Dialogue
    ## --------

    def load_dialogue_overlay(self):

        self.dialogue_overlay = self.interface.add(
            width = 1.0,
            height = 1.0,
            align_x = 0.5,
            align_y = 0.5,
            background_color = (0, 0, 0, 240),
            visible = False,
        )

        self.character_left = self.dialogue_overlay.add(
            width = 0.25,
            height = 0.5,
            align_x = 0.15,
            align_y = 0.3,
            anchor_y = 0.0,
        )

        self.name_left = self.character_left.add(
            width = 1.0,
            height = 0.15,
            align_x = 0.5,
            align_y = 0.15,
            text = 'Character Name',
            text_color = (255, 255, 255, 255),
            text_bold = True,
            text_wrap = False,
            font_size = 0.03,
            visible = False,
        )

        self.character_right = self.dialogue_overlay.add(
            width = 0.25,
            height = 0.5,
            align_x = 0.85,
            align_y = 0.3,
            anchor_y = 0.0,
        )

        self.name_right = self.character_right.add(
            width = 1.0,
            height = 0.15,
            align_x = 0.5,
            align_y = 0.15,
            text = 'Character Name',
            text_color = (255, 255, 255, 255),
            text_bold = True,
            text_wrap = False,
            font_size = 0.03,
            visible = False,
        )

        self.message_container = self.dialogue_overlay.add(
            width = 0.9,
            height = 0.25,
            padding = 0.02,
            align_x = 0.5,
            align_y = 0.3,
            anchor_y = 1.0,
            background_color = (200, 50, 50, 255),
            frame_texture = pyglet.resource.texture('interface/dialogue_border.png'),
        )

        self.message_area = self.message_container.add(
            align_y = 1.0,
            align_x = 0.0,
            text_color = (255, 255, 255, 255),
            font_size = 0.03,
        )

        self.message_area.text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec neque ut metus suscipit pretium vel sit amet nulla. Sed rhoncus scelerisque nunc, in lobortis risus tempus in. Nullam vitae nunc ipsum. Quisque sit amet mattis nunc, non dapibus massa. Ut porta ex quis sem tempor aliquam. Fusce semper cursus elit, iaculis rhoncus magna accumsan nec. Maecenas sagittis tempus ligula at congue.'

        self.scene_lines = None

    def start_scene(self, name):
        self.scene_lines = pyglet.resource.file(f'scenes/{name}.txt', 'r').readlines()
        self.dialogue_overlay.visible = True
        self.advance_scene()

    def advance_scene(self):
        while len(self.scene_lines) > 0:
            line = self.scene_lines.pop(0).strip()
            if len(line) == 0:
                continue
            command, value = map(str.strip, line.split(':', 1))

            if command == 'set_left_image':
                if len(value) > 0:
                    self.character_left.image_texture = pyglet.resource.texture(f'characters/{value}.png')
                else:
                    self.character_left.image_texture = None
            if command == 'set_right_image':
                if len(value) > 0:
                    self.character_right.image_texture = pyglet.resource.texture(f'characters/{value}.png')
                else:
                    self.character_right.image_texture = None

            if command == 'set_left_name':
                self.name_left.text = value or None
            if command == 'set_right_name':
                self.name_right.text = value or None

            if command == 'say_left':
                self.message_area.text = value
                self.name_left.visible = True
                self.name_right.visible = False
                self.character_left.image_color = (255, 255, 255, 255)
                self.character_right.image_color = (75, 75, 75, 255)
                break
            if command == 'say_right':
                self.message_area.text = value
                self.name_right.visible = True
                self.name_left.visible = False
                self.character_right.image_color = (255, 255, 255, 255)
                self.character_left.image_color = (75, 75, 75, 255)
                break
        else:
            self.scene_lines = None
            self.dialogue_overlay.visible = False

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
            if sprite._can_click_through:
                continue
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
        if self.dialogue_overlay.visible:
            pass
        else:
            self._update_mouse_position(x, y)

    def on_mouse_leave(self, x, y):
        if self.dialogue_overlay.visible:
            pass
        else:
            self._update_mouse_position(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.dialogue_overlay.visible:
            pass
        else:
            self._update_mouse_position(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.dialogue_overlay.visible:
            pass
        else:
            self._update_mouse_position(x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.dialogue_overlay.visible:
            pass
        else:
            self._update_mouse_position(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.dialogue_overlay.visible:
            pass
        else:
            self._update_mouse_position(x, y)
            self._clicked_sprite = self._target_sprite

    def on_mouse_release(self, x, y, button, modifiers):
        if self.dialogue_overlay.visible:
            self.advance_scene()
        else:
            self._update_mouse_position(x, y)
            if self._clicked_sprite is not None:
                if self._target_sprite is self._clicked_sprite:
                    # Zhu Li, do the thing!
                    target = self.entities_by_sprite[self._clicked_sprite]
                    if self._is_interactable(target):
                        self.level.interact(target)
                        sound.pop()
                self._clicked_sprite = None

    ## Debugging
    ## ---------

    def on_key_press(self, symbol, modifiers):
        if DEBUG and symbol == pyglet.window.key.L:
            self.level.debug_print()
        if DEBUG and symbol == pyglet.window.key.D:
            self.start_scene('example')

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
            cursor_y = cursor_texture.height / 2
            cursor = ScaledImageMouseCursor(cursor_texture, cursor_height, cursor_x, cursor_y)
            self._cursor_cache[cursor_texture] = cursor
        else:
            cursor = self._cursor_cache[cursor_texture]

        # Set the cursor on the window.
        app.window.set_mouse_cursor(cursor)

    def on_draw(self):

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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

        self.draw_progress_bars()

    def draw_progress_bars(self):
        view_width, view_height = self.interface.get_content_size()
        offset_x, offset_y = self.interface.get_offset()
        
        left_bar_progress = 0.5
        left_bar_left = offset_x + PROGRESS_BAR_MARGIN * view_height
        left_bar_right = left_bar_left + PROGRESS_BAR_WIDTH * view_width
        left_bar_top = offset_y + view_height - PROGRESS_BAR_MARGIN * view_height
        left_bar_bottom = left_bar_top - PROGRESS_BAR_HEIGHT * view_height
        left_bar_filled_right = left_bar_left + (left_bar_right - left_bar_left) * left_bar_progress
        left_bar_filled_right_slope = min(left_bar_right, left_bar_filled_right + (left_bar_top - left_bar_bottom))
        pyglet.graphics.draw(8, GL_QUADS,
            ('v2f', [
                left_bar_left, left_bar_bottom,
                left_bar_right, left_bar_bottom,
                left_bar_right, left_bar_top,
                left_bar_left, left_bar_top,
                left_bar_left, left_bar_bottom,
                left_bar_filled_right_slope, left_bar_bottom,
                left_bar_filled_right, left_bar_top,
                left_bar_left, left_bar_top,
            ]),
            ('c4B', [255, 255, 255, 255] * 4 + [0, 0, 255, 255] * 4)
        )
        
        right_bar_progress = 0.5
        right_bar_right = offset_x + view_width - PROGRESS_BAR_MARGIN * view_height
        right_bar_left = right_bar_right - PROGRESS_BAR_WIDTH * view_width
        right_bar_top = offset_y + view_height - PROGRESS_BAR_MARGIN * view_height
        right_bar_bottom = right_bar_top - PROGRESS_BAR_HEIGHT * view_height
        right_bar_filled_left = right_bar_right - (right_bar_right - right_bar_left) * right_bar_progress
        right_bar_filled_left_slope = max(right_bar_left, right_bar_filled_left - (right_bar_top - right_bar_bottom))
        pyglet.graphics.draw(8, GL_QUADS,
            ('v2f', [
                right_bar_left, right_bar_bottom,
                right_bar_right, right_bar_bottom,
                right_bar_right, right_bar_top,
                right_bar_left, right_bar_top,
                right_bar_filled_left_slope, right_bar_bottom,
                right_bar_right, right_bar_bottom,
                right_bar_right, right_bar_top,
                right_bar_filled_left, right_bar_top,
            ]),
            ('c4B', [255, 255, 255, 255] * 4 + [0, 0, 255, 255] * 4)
        )


    def draw_customer_overlay(self, sprite):
        customer = self.entities_by_sprite.get(sprite)
        if (customer is not None) and (customer.level is not None):
            view_width, view_height = self.interface.get_content_size()
            sprite = customer.sprite
            bar_margin = view_height * CUSTOMER_PATIENCE_BAR_MARGIN
            bar_height = view_height * CUSTOMER_PATIENCE_BAR_HEIGHT
            bar_x = sprite.x + sprite.animation_offset_x - sprite.width / 2 + bar_margin
            bar_y = view_height * (0.5 + CUSTOMER_PATIENCE_BAR_VERTICAL_OFFSET) + bar_margin - bar_height / 2
            bar_width = sprite.width - 2 * bar_margin
            bar_full_width = bar_width * customer.get_patience_ratio()
            pyglet.graphics.draw(8, GL_QUADS,
                ('v2f', [
                    bar_x, bar_y,
                    bar_x + bar_width, bar_y,
                    bar_x + bar_width, bar_y + bar_height,
                    bar_x, bar_y + bar_height,
                    bar_x, bar_y,
                    bar_x + min(bar_width, bar_full_width + bar_height), bar_y,
                    bar_x + bar_full_width, bar_y + bar_height,
                    bar_x, bar_y + bar_height,
                ]),
                ('c4B', [255, 255, 255, 255] * 4 + [0, 0, 255, 255] * 4)
            )

