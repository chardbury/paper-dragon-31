'''applib.scenes.level -- level scene

'''

import math
import pprint
import random
import time

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
from applib.constants import CUSTOMER_PATIENCE_COLOURS
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


class HeldItemMouseCursor(pyglet.window.ImageMouseCursor):

    def __init__(self, scene, height, image, hot_x=0.0, hot_y=0.0):
        super().__init__(image, hot_x, hot_y)
        self.scene = scene
        self.height = height
    
    def draw(self, x, y):
        hot_x = self.hot_x
        hot_y = self.hot_y

        held = self.scene.level.held_item
        if held is None:
            texture = self.texture
            return
        else:
            texture = held.sprite._texture

        rel_x, rel_y = held.center_position
        hot_x += rel_x * texture.width
        hot_y += rel_y * texture.height

        # Compute the coordinates of the cursor box.
        scale = self.height / texture.height
        x1 = x - hot_x * scale
        y1 = y - hot_y * scale
        x2 = x1 + texture.width * scale
        y2 = y1 + texture.height * scale

        # Render the texture in the cursor box.
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(texture.target)
        glBindTexture(texture.target, texture.id)
        pyglet.graphics.draw_indexed(4, GL_TRIANGLES,
            [0, 1, 2, 0, 2, 3],
            ('v2f', [x1, y1, x2, y1, x2, y2, x1, y2]),
            ('t3f', texture.tex_coords),
            ('c4B', [255] * 16),
        )
        glPopAttrib()

        if held.holds:
            subtexture = held.holds.sprite._texture
            off_x, off_y = held.holds_position
            off_x *= held.sprite.width
            off_y *= held.sprite.height
            scale = self.height / subtexture.height
            x1 = x - hot_x * scale + off_x
            y1 = y - hot_y * scale + off_y
            x2 = x1 + subtexture.width * scale
            y2 = y1 + subtexture.height * scale
            glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glEnable(subtexture.target)
            glBindTexture(subtexture.target, subtexture.id)
            pyglet.graphics.draw_indexed(4, GL_TRIANGLES,
                [0, 1, 2, 0, 2, 3],
                ('v2f', [x1, y1, x2, y1, x2, y2, x1, y2]),
                ('t3f', subtexture.tex_coords),
                ('c4B', [255] * 16),
            )
            glPopAttrib()

        # if DEBUG:
        #     s = self.height / 10.0
        #     pyglet.graphics.draw_indexed(4, GL_TRIANGLES,
        #         [0, 1, 2, 0, 2, 3],
        #         ('v2f', [x-s, y, x, y-s, x+s, y, x, y+s]),
        #         ('c4B', [0, 255, 0, 127] * 4),
        #     )


class LevelScene(object):
    '''Class comprising the main interface to `applib.model.level.Level`.

    '''

    def __init__(self, level=None):
        '''Create a `LevelScene` object.

        '''

        # Ensure we have an appropriate level.
        if level is None:
            if app.settings.level < 0:
                level = applib.model.level.TestLevel
            else:
                level = applib.model.level.default_level
                for _ in range(app.settings.level - 1):
                    level = level.next_level
        self.level = level()
        applib.model.scenery.Counter(self.level)
        self.level.background_scenery(self.level)
        
        self.level.push_handlers(self)

        # Create the root interface panel.
        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background_color = (255, 255, 255, 255),
        )

        
        self.bg_player = {
            applib.model.scenery.BackgroundVillage: applib.engine.sound.bg_mix_village,
            applib.model.scenery.BackgroundHill: applib.engine.sound.bg_mix_hill,
        }[self.level.background_scenery]()

        self.overlay = self.interface.add(
            draw_function = self.draw_overlay,
        )

        self.scene_fade = 1.0
        self.fade_animation = animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 0.0, 1.0),
        ).start()
        self.dialogue_animation = None
        app.music.switch(None)

        self.load_level_sprites()

        self.load_dialogue_overlay()
        self.on_tick()
        self.start_scene(self.level.opening_scene)
        self.paw_animations = {}

    def on_scene_end(self):
        self.bg_player.pause()

    ## Model
    ## -----

    def load_level_sprites(self):
        self.sprites_by_entity = {}
        self.entities_by_sprite = {}
        self.persisting_sprites = {}
        for entity in self.level.entities:
            self.update_sprite(entity)

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

            # Cache the texture data for alpha hit testing.
            if texture not in self._texture_data:
                texture_data = texture.get_image_data().get_data()
                self._texture_data[texture] = texture_data

            # Process any alternative sprites early.
            for alt_sprite_paths in getattr(entity, 'alt_sprites', {}).values():
                for alt_sprite_path in alt_sprite_paths:
                    alt_texture = pyglet.resource.texture(alt_sprite_path)
                    if alt_texture not in self._texture_data:
                        texture_data = texture.get_image_data().get_data()
                        self._texture_data[alt_texture] = texture_data
                    alt_texture.anchor_x = alt_texture.width // 2
                    alt_texture.anchor_y = alt_texture.height // 2

            # Update the sprite indexes.
            self.sprites_by_entity[entity] = sprite
            self.entities_by_sprite[sprite] = entity

            # Ensure the sprite is in the interface
            if sprite not in self.interface.sprites:
                self.interface.sprites.append(sprite)
                sprite._can_click_through = isinstance(entity, applib.model.item.Item)
            
                # Get the proprties used to configure the sprite.
                for entity_class, relative_height, sprite_layer in self._entity_properties:
                    if isinstance(entity, entity_class):
                        break

                # Configure the sprite and its texture.
                texture.anchor_x = texture.width // 2
                texture.anchor_y = texture.height // 2
                sprite.scale_x = (relative_height * view_height) / texture.height
                sprite.scale_y = (relative_height * view_height) / texture.height
                if sprite_layer is not None:
                    sprite.layer = sprite_layer
                elif hasattr(entity, 'get_layer'):
                    sprite.layer = entity.get_layer()

                # Position the sprite.
                if move_x is not None:
                    sprite.x = view_width / 2 + move_x * view_height
                if move_y is not None:
                    sprite.y = view_height / 2 + move_y * view_height

                if sprite.x > view_width / 2 and sprite.scale_x > 0:
                    sprite.scale_x *= -1

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
                customer.sprite.animation_offset_x = view_width / 2

    def on_customer_leaves(self, customer):
        view_width, view_height = self.interface.get_content_size()

        # Have the leaving customer walk off.
        customer.sprite.layer = -1.5
        customer.sprite._target_offset_x = -view_width
        self.persisting_sprites[customer.sprite] = (lambda c=customer:
            abs(c.sprite.animation_offset_x) > view_width / 2)

        # Have the remaining customers reposition.
        customer_count = len(self.level.customers)
        for index, other_customer in enumerate(self.level.customers):
            move_x = CUSTOMER_POSITIONS[customer_count][index]
            if other_customer is not customer:
                other_customer.sprite.layer = -1
                other_customer.sprite._target_offset_x = move_x * view_height

    def _stop_device_sounds(self):
        for device in self.level.devices:
            if device._sound_player:
                device._sound_player.next_source()

    def on_level_success(self):
        self.start_scene(self.level.victory_scene, 1.0)
        sound.success()

    def on_level_fail(self):
        self.start_scene(self.level.failure_scene, 1.0)
        sound.sad_trombone()

    fade_animation = None

    def on_tick(self):
        if self.scene_fade > 0.0:
            return

        if self.dialogue_overlay.visible:
            # Do dialogue things here.
            pass
        else:
            # Update the level first.
            self.level.tick()

        view_width, view_height = self.interface.get_content_size()

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
                if sprite in self.entities_by_sprite:
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
                    item.sprite.layer = sprite.layer + 0.2
                    item.sprite.update(
                        x = position_x,
                        y = position_y,
                        scale = 0.7,
                        rotation = order_arc_angle,
                    )
                    bubble = pyglet.resource.texture('interface/bubble.png')
                    item.sprite.set_background_sprite(bubble)
                    item.sprite.update_background_sprite()

                # Paw animation
                paw_name = f'customers/{entity.name}_paw.png'
                if paw_name in pyglet.resource._default_loader._index:
                    if not sprite.foreground_sprite:
                        texture = pyglet.resource.texture(paw_name)
                        sprite.set_foreground_sprite(texture)
                        fg = sprite.foreground_sprite
                        fg.visible = False
                        fg.layer = sprite.layer
                        self.persisting_sprites[fg] = (lambda c=entity:
                            abs(c.sprite.animation_offset_x) > view_width / 2)
                        self.interface.sprites.append(fg)
                    sprite.update_foreground_sprite()
                    fg = sprite.foreground_sprite

                    customer_is_moving = (sprite._animation_offset_x != sprite._target_offset_x)
                    paws_on_counter = (fg.animation_offset_y == 0.0 and fg.layer == 0.1)
                    paws_are_animating = (entity in self.paw_animations) and (self.paw_animations[entity] in app.animation)
                    customer_is_on_right = (entity in self.level.customers) and (self.level.customers.index(entity) > 2)

                    if not paws_are_animating:
                        if customer_is_moving and paws_on_counter:
                            # Animate off counter
                            fg.visible = True
                            fg.animation_offset_y = 0.0
                            fg.layer = 0.1
                            self.paw_animations[entity] = animation.QueuedAnimation(
                                animation.AttributeAnimation(fg, 'animation_offset_y', 0.03 * fg.height, 0.4, 'symmetric'),
                                animation.WaitAnimation(0.0, lambda fg=fg, sp=sprite: setattr(fg, 'layer', sp.layer+0.1)),
                                animation.AttributeAnimation(fg, 'animation_offset_y', -0.1 * fg.height, 0.8, 'symmetric'),
                            ).start()
                        elif not customer_is_moving and not paws_on_counter and not customer_is_on_right:
                            # Animate on counter
                            fg.visible = True
                            fg.animation_offset_y = -0.1 * fg.height
                            fg.layer = sprite.layer + 0.1
                            self.paw_animations[entity] = animation.QueuedAnimation(
                                animation.AttributeAnimation(fg, 'animation_offset_y', 0.03 * fg.height, 0.8, 'symmetric'),
                                animation.WaitAnimation(0.0, lambda fg=fg: setattr(fg, 'layer', 0.1)),
                                animation.AttributeAnimation(fg, 'animation_offset_y', 0.0, 0.4, 'symmetric'),
                            ).start()
                        
            
            # Move current item sprites to their device.
            if isinstance(entity, applib.model.device.Device):

                # Set alternative texture
                has_alt_sprite = False
                if type(entity.current_item) in entity.alt_sprites:
                    alt_index = int(time.time() * 5) % len(entity.alt_sprites[type(entity.current_item)])
                    alt_texture_path = entity.alt_sprites[type(entity.current_item)][alt_index]
                    texture = pyglet.resource.texture(alt_texture_path)
                    sprite._texture.anchor_x = sprite._texture.width // 2
                    sprite._texture.anchor_y = sprite._texture.height // 2
                    if texture not in self._texture_data:
                        texture_data = texture.get_image_data().get_data()
                        self._texture_data[texture] = texture_data
                    has_alt_sprite = True
                else:
                    texture = entity.texture
                if texture != sprite._texture:
                    sprite._set_texture(texture)
                    sprite._update_position()

                if entity.sprite.x > view_width / 2 and entity.sprite.scale_x > 0:
                    entity.sprite.scale_x *= -1
                if entity.current_item is not None:
                    processed_items.append(entity.current_item)
                    flipped = (entity.sprite.x > view_width / 2)
                    item_x, item_y = entity.item_position
                    entity.current_item.sprite.layer = sprite.layer + 0.2
                    entity.current_item.sprite.visible = not has_alt_sprite
                    entity.current_item.sprite.update(
                        x = sprite.x + item_x * sprite.width * (-1 if flipped else 1),
                        y = sprite.y + item_y * sprite.height,
                    )

        # Postprocessing for items.
        for sprite, entity in self.entities_by_sprite.items():
            if isinstance(entity, applib.model.item.Item):
                if entity.holds is not None:
                    processed_items.append(entity.holds)
                    hold_sprite = entity.holds.sprite
                    item_x, item_y = entity.holds_position
                    entity.holds.sprite.layer = sprite.layer + 0.2
                    entity.holds.sprite.visible = (entity is not self.level.held_item)
                    entity.holds.sprite.update(
                        x = sprite.x + item_x * sprite.width,
                        y = sprite.y + item_y * sprite.height,
                    )

        # Postpostprocessing for items.
        for sprite, entity in self.entities_by_sprite.items():
            if isinstance(entity, applib.model.item.Item):
                if entity not in processed_items:
                    sprite.visible = True
                    if entity is self.level.held_item:
                        sprite.visible = False
                    elif DEBUG:
                        self.level.debug_print()

    ## Dialogue
    ## --------

    def load_dialogue_overlay(self):
        
        applib.scenes.victory.make_dialogue_interface(self)

        self.scene_lines = None

    def start_scene(self, name, slowly=None):
        if name is not None:
            self._stop_device_sounds()
            self.name_left.text_update(None)
            self.name_right.text_update(None)
            self.name_left.visible = False
            self.name_right.visible = False
            self.character_left.image_texture = None
            self.character_right.image_texture = None
            self.message_container.visible = False
            self.message_area.text_update(None)
            self.scene_lines = pyglet.resource.file(f'scenes/{name}.txt', 'r').readlines()
            self.dialogue_overlay.visible = True
            if slowly is not None:
                self.dialogue_overlay.background_opacity = 0.0
                self.dialogue_animation = animation.QueuedAnimation(
                    animation.AttributeAnimation(self.dialogue_overlay, 'background_opacity', 0.8, slowly, 'symmetric'),
                    animation.WaitAnimation(0.3, self.advance_scene),
                ).start()
            else:
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
                self.name_left.text_update(value or None)
            if command == 'set_right_name':
                self.name_right.text_update(value or None)

            if command == 'say_left':
                self.message_container.visible = True
                self.message_area.text_update(value)
                self.name_left.visible = bool(self.name_left.text)
                self.name_right.visible = False
                self.character_left.image_color = (255, 255, 255, 255)
                self.character_right.image_color = (75, 75, 75, 255)
                break
            if command == 'say_right':
                self.message_container.visible = True
                self.message_area.text_update(value)
                self.name_right.visible = bool(self.name_right.text)
                self.name_left.visible = False
                self.character_right.image_color = (255, 255, 255, 255)
                self.character_left.image_color = (75, 75, 75, 255)
                break

            if command == 'next_level':
                if value:
                    next_level = getattr(applib.model.level, value)
                else:
                    next_level = self.level.next_level
                self.fade_animation = animation.QueuedAnimation(
                    animation.AttributeAnimation(self, 'scene_fade', 1.0, 1.0),
                    animation.WaitAnimation(0.5, app.controller.switch_scene, type(self), next_level)
                ).start()
                break

            if command == 'repeat_level':
                self.fade_animation = animation.QueuedAnimation(
                    animation.AttributeAnimation(self, 'scene_fade', 1.0, 1.0),
                    animation.WaitAnimation(0.5, app.controller.switch_scene, type(self), type(self.level)),
                ).start()
                break

            if command == 'win_game':
                self.fade_animation = animation.QueuedAnimation(
                    animation.AttributeAnimation(self, 'scene_fade', 1.0, 1.0),
                    animation.WaitAnimation(0.5, app.controller.switch_scene, applib.scenes.victory.VictoryScene),
                ).start()
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
        return hasattr(entity, 'interact') and (entity.level is self.level)

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
            if getattr(sprite, '_can_click_through', True):
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
                    relative_x = texture_x / texture.width
                    relative_y = texture_y / texture.height
                    return sprite, relative_x, relative_y
        return None, 0.0, 0.0
    
    def _update_mouse_position(self, mouse_x, mouse_y):
        '''Update the mouse position and record the targeted sprite.

        '''
        self._mouse_x, self._mouse_y = mouse_x, mouse_y
        new_target_sprite, relative_x, relative_y = self._get_sprite_at(mouse_x, mouse_y)
        if new_target_sprite != self._target_sprite:
            self._change_sprite_focus(new_target_sprite, self._target_sprite)
            self._target_sprite = new_target_sprite
        self._target_relative_x = relative_x
        self._target_relative_y = relative_y

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
                        # Check for plating subpositions.
                        if isinstance(target, applib.model.device.MultiPlating):
                            relative_x = self._target_relative_x
                            relative_y = self._target_relative_y
                            best_index = best_distance = None
                            for index, (pos_x, pos_y) in enumerate(target.subpositions):
                                distance = math.hypot(pos_x + 0.5 - relative_x, pos_y + 0.5 - relative_y)
                                if (best_distance is None) or (distance < best_distance):
                                    best_distance = distance
                                    best_index = index
                            target = target.subdevices[best_index]
                        self.level.interact(target)
                self._clicked_sprite = None

    ## Debugging
    ## ---------

    def on_key_press(self, symbol, modifiers):
        if DEBUG and symbol == pyglet.window.key.L:
            self.level.debug_print()
        if DEBUG and symbol == pyglet.window.key.D:
            self.start_scene('example')
        if DEBUG and symbol == pyglet.window.key.F:
            self.level.dispatch_event('on_level_fail')
        if DEBUG and symbol == pyglet.window.key.W:
            self.level.dispatch_event('on_level_success')
        if DEBUG and symbol == pyglet.window.key.T:
            app.controller.switch_scene(LevelScene, applib.model.level.TestLevel)

    ## Rendering
    ## ---------

    _held_item_cursor = None

    def set_cursor(self):
        if self.level.held_item:
            if self._held_item_cursor is None:
                cursor_texture = self.level.held_item.sprite._texture
                view_width, view_height = self.interface.get_content_size()
                cursor_height = CURSOR_SCALE * view_height
                cursor_x = cursor_texture.width / 2
                cursor_y = cursor_texture.height / 2
                self._held_item_cursor = HeldItemMouseCursor(self, cursor_height, cursor_texture, cursor_x, cursor_y)
            app.window.set_mouse_cursor(self._held_item_cursor)
        else:
            app.window.set_mouse_cursor(None)

    def on_draw(self):

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Clear the buffers.
        app.window.clear()
        
        x, y = map(int, self.interface.get_offset())
        w, h = map(int, self.interface.get_content_size())
        glEnable(GL_SCISSOR_TEST)
        glScissor(x, y, w, h)

        self.set_cursor()

        # Order the sprites for rendering.
        layer_key = (lambda sprite: sprite.layer)
        self.interface.sprites.sort(key=layer_key)

        # Render the interface.
        self.interface.draw()

        # # Render texture overlay
        # overlay_texture = pyglet.resource.texture('overlays/burlap_256.png')
        # glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        # glEnable(overlay_texture.target)
        # glBindTexture(overlay_texture.target, overlay_texture.id)
        # glTexParameteri(overlay_texture.target, GL_TEXTURE_WRAP_S, GL_REPEAT)
        # glTexParameteri(overlay_texture.target, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # x, y = map(int, self.interface.get_offset())
        # w, h = map(int, self.interface.get_content_size())
        # x, y = 0, 0
        # w, h = app.window.get_size()
        # vertex_data = [x, y, x + w, y, x + w, y + h, x, y + h]
        # texture_data = [v / overlay_texture.width for v in [x, y, x + w, y, x + w, y + h, x, y + h]]
        # color_data = [255, 255, 255, 255] * 4
        # pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t2f', texture_data), ('c4B', color_data))
        # glPopAttrib()

        # Render fade
        if self.scene_fade > 0.0:
            w, h = app.window.get_size()
            alpha = max(0, min(255, int(256*self.scene_fade)))
            color = [0, 0, 0, alpha]
            pyglet.graphics.draw(4, GL_QUADS, ('v2f', [0,0,w,0,w,h,0,h]), ('c4B', color*4))

        glDisable(GL_SCISSOR_TEST)

    def draw_overlay(self, draw_x, draw_y):
        view_width, view_height = self.interface.get_content_size()

        def make_rect(x, y, w, h):
            return [x, y, x + w, y, x + w, y + h, x, y + h]

        # Suspicion on left!

        bg_texture = pyglet.resource.texture('interface/sus_bg.png')
        fg_texture = pyglet.resource.texture('interface/sus_fg.png')
        width = PROGRESS_BAR_WIDTH * view_width
        height = width * bg_texture.height / bg_texture.width
        left = draw_x
        bottom = draw_y + view_height - height
        vertex_data = make_rect(left, bottom, width, height)

        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(bg_texture.target)
        glBindTexture(bg_texture.target, bg_texture.id)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t3f', bg_texture.tex_coords), ('c4B', [255] * 16))
        glPopAttrib()

        progress = max(0.0, min(1.0, self.level.get_score_ratio()))
        left_offset = 0.15
        bottom_offset = 0.25
        right_offset = 0.12
        top_offset = 0.25
        top_right_slope_threshold = 0.22
        fill_width = max(0, (width - (left_offset + right_offset) * height) * progress)
        vertex_data_filled = make_rect(
            left + left_offset * height,
            bottom + bottom_offset * height,
            fill_width,
            height - (bottom_offset + top_offset) * height,
        )
        vertex_data_filled[4] = min(vertex_data_filled[4], left + width - top_right_slope_threshold * width)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data_filled), ('c4B', [0, 0, 255, 255] * 4))

        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(fg_texture.target)
        glBindTexture(fg_texture.target, fg_texture.id)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t3f', fg_texture.tex_coords), ('c4B', [255] * 16))
        glPopAttrib()

        # Heist on right!

        bg_texture = pyglet.resource.texture('interface/heist_bg.png')
        fg_texture = pyglet.resource.texture('interface/heist_fg.png')
        width = PROGRESS_BAR_WIDTH * view_width
        height = width * bg_texture.height / bg_texture.width
        left = draw_x + view_width - width
        bottom = draw_y + view_height - height
        vertex_data = make_rect(left, bottom, width, height)

        tx = bg_texture.tex_coords
        tex_coords = [
            tx[3], tx[4], tx[5],
            tx[0], tx[1], tx[2],
            tx[9], tx[10], tx[11],
            tx[6], tx[7], tx[8],
        ]
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(bg_texture.target)
        glBindTexture(bg_texture.target, bg_texture.id)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t3f', tex_coords), ('c4B', [255] * 16))
        glPopAttrib()

        progress = max(0.0, min(1.0, self.level.get_time_ratio()))
        right_offset = 0.15
        bottom_offset = 0.25
        left_offset = 0.12
        top_offset = 0.25
        top_left_slope_threshold = 0.22
        fill_width = max(0, (width - (left_offset + right_offset) * height) * progress)
        vertex_data_filled = make_rect(
            left + width - right_offset * height - fill_width,
            bottom + bottom_offset * height,
            fill_width,
            height - (bottom_offset + top_offset) * height,
        )
        vertex_data_filled[6] = max(vertex_data_filled[6], left + top_left_slope_threshold * width)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data_filled), ('c4B', [0, 0, 255, 255] * 4))

        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(fg_texture.target)
        glBindTexture(fg_texture.target, fg_texture.id)
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t3f', tex_coords), ('c4B', [255] * 16))
        glPopAttrib()

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
            color = CUSTOMER_PATIENCE_COLOURS[customer.get_score_bracket()]
            bg_texture = pyglet.resource.texture('interface/white_fade_bg.png')
            fg_texture = pyglet.resource.texture('interface/white_fade_bg.png')
            self.draw_frame(bg_texture, bar_x, bar_y, bar_width, bar_height, bar_height / 2)
            pyglet.graphics.draw(8, GL_QUADS,
                ('v2f', [
                    bar_x, bar_y,
                    bar_x + bar_width, bar_y,
                    bar_x + bar_width, bar_y + bar_height,
                    bar_x, bar_y + bar_height,
                    bar_x, bar_y,
                    bar_x + bar_full_width, bar_y,
                    bar_x + bar_full_width, bar_y + bar_height,
                    bar_x, bar_y + bar_height,
                ]),
                ('c4B', [255] * 4 * 4 + color * 4)
            )
            self.draw_frame(fg_texture, bar_x, bar_y, bar_width, bar_height, bar_height / 2)

    def draw_frame(self, texture, left, bottom, width, height, size):
        def make_rect(x, y, w, h):
            return (x, y, x + w, y, x + w, y + h, x, y + h)
        vertex_data = (
            make_rect(left - size/2, bottom - size/2, size, size) +
            make_rect(left + width - size/2, bottom - size/2, size, size) +
            make_rect(left + width - size / 2, bottom + height - size / 2, size, size) +
            make_rect(left - size / 2, bottom + height - size / 2, size, size)
        )
        tx1, ty1 = texture.tex_coords[0:2]
        tx2, ty2 = texture.tex_coords[6:8]
        txm = (tx1 + tx2) / 2
        tym = (ty1 + ty2) / 2
        texture_data = (
            tx1, ty1, txm, ty1, txm, tym, tx1, tym,
            txm, ty1, tx2, ty1, tx2, tym, txm, tym,
            txm, tym, tx2, tym, tx2, ty2, txm, ty2,
            tx1, tym, txm, tym, txm, ty2, tx1, ty2,
        )
        color_data = (255, 255, 255, 255) * 16
        indices = (
            0, 1, 3, 2, 12, 13,
            15, 13, 14, 13, 11, 8,
            10, 8, 9, 8, 6, 7,
            5, 7, 4, 7, 1, 2,
            #2, 7, 13, 8,
        )
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(texture.target)
        glBindTexture(texture.target, texture.id)
        pyglet.graphics.draw_indexed(16, GL_TRIANGLE_STRIP, indices,
            ('v2f', vertex_data), ('t2f', texture_data), ('c4B', color_data))
        glPopAttrib()
