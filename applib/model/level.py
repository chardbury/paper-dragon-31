'''applib.model.level -- self-contained game level

'''

import math
import random

import applib
import pyglet

from applib.constants import TICK_LENGTH
from applib.constants import TICK_RATE
from applib.constants import MAX_SCORE_FROM_CUSTOMER
from applib.model import device
from applib.model import entity
from applib.model import item
from applib.model import scenery


class Order(object):

    def __init__(self, *items):
        self.items = list(items)

    def remove(self, match_item):
        for index, item in enumerate(self.items):
            if item.matches(match_item):
                self.items.pop(index).destroy()
                return True
            if match_item and match_item.holds and item.matches(match_item.holds):
                self.items.pop(index).destroy()
                return True
        return False


class Customer(entity.Entity):

    group = 'customers'

    customer_patience = {
        'cop_dog': 15,
        'cop_elephant': 50,
        'cop_rabbit': 30,
        'friend_patches': 120,
        'slacker_patches': 5,
    }

    customer_sounds = {
        'cop_dog': {
            'hello': applib.engine.sound.dog_hello,
            'no': applib.engine.sound.dog_neg,
            'yes': applib.engine.sound.dog_pos,
        },
        'cop_elephant': {
            'hello': applib.engine.sound.elephant_hello,
            'no': applib.engine.sound.elephant_neg,
            'yes': applib.engine.sound.elephant_pos,
        },
        'cop_rabbit': {
            'hello': applib.engine.sound.rabbit_hello,
            'no': applib.engine.sound.rabbit_neg,
            'yes': applib.engine.sound.rabbit_pos,
        },
        'friend_patches': {
            'hello': applib.engine.sound.patches_hello,
            'no': applib.engine.sound.patches_neg,
            'yes': applib.engine.sound.patches_pos,
        },
        'slacker_patches': {
            'hello': applib.engine.sound.patches_hello,
            'no': applib.engine.sound.patches_neg,
            'yes': applib.engine.sound.patches_pos,
        },
    }

    def sound_hello(self, *args, **kwargs):
        self.customer_sounds[self.name]['hello']()

    def sound_yes(self, *args, **kwargs):
        self.customer_sounds[self.name]['yes']()

    def sound_no(self, *args, **kwargs):
        self.customer_sounds[self.name]['no']()

    def __init__(self, level, order, customer_type=None):
        if customer_type is None:
            self.name = random.choice(list(self.customer_patience))
        else:
            self.name = customer_type
        super().__init__(level)
        self.order = order
        self.patience_ticks = self.compute_patience()

    @property
    def texture(self):
        if (self._texture is None) and (self.group is not None) and (self.name is not None):
            self._texture = pyglet.resource.texture(f'{self.group}/{self.name}.png')
        return self._texture

    def destroy(self):
        super().destroy()
        for item in self.order.items:
            item.destroy()

    def compute_patience(self):
        '''Return the patience in ticks

        '''
        self.start_patience = self.customer_patience[self.name]
        self.start_patience_ticks = int(math.ceil(self.start_patience // TICK_LENGTH))
        return self.start_patience_ticks

    def get_patience_ratio(self):
        return (self.patience_ticks / self.start_patience_ticks)

    def interact(self, held_item):
        if self.order.remove(held_item):
            if isinstance(held_item, item.Plate):
                self.patience_ticks = min(self.start_patience_ticks, self.patience_ticks + self.start_patience_ticks / 5)
            held_item.destroy()
            self.sound_yes()
        else:
            self.sound_no()
            return held_item

    def get_score_bracket(self):
        percentage_remaining_patience = self.get_patience_ratio() * 100
        if self.level.serve_style == 'slow':
            if percentage_remaining_patience >= 80:
                score = 0
            elif percentage_remaining_patience >= 40:
                score = 1
            elif percentage_remaining_patience >= 20:
                score = 2
            elif percentage_remaining_patience >= 5:
                score = 3
            else:
                score = 4
        elif self.level.serve_style == 'fast':
            if percentage_remaining_patience >= 80:
                score = 4
            elif percentage_remaining_patience >= 40:
                score = 3
            elif percentage_remaining_patience >= 20:
                score = 2
            elif percentage_remaining_patience >= 5:
                score = 1
            else:
                score = 0
        return score
    
    def compute_score(self):
        bracket = self.get_score_bracket()
        if self.level.alt_suspicion_mode:
            bracket = min(3, 4 - bracket)
            if bracket == 3:
                return MAX_SCORE_FROM_CUSTOMER * 0.25
            elif bracket == 2:
                return MAX_SCORE_FROM_CUSTOMER * 0.375
            elif bracket == 1:
                return MAX_SCORE_FROM_CUSTOMER * 0.5
            else:
                return MAX_SCORE_FROM_CUSTOMER * 0.75
        else:
            if bracket == 4:
                return 0
            elif bracket == 3:
                return MAX_SCORE_FROM_CUSTOMER * 0.125
            elif bracket == 2:
                return MAX_SCORE_FROM_CUSTOMER * 0.25
            elif bracket == 1:
                return MAX_SCORE_FROM_CUSTOMER * 0.5
            else:
                return MAX_SCORE_FROM_CUSTOMER * 0.75

    def tick(self):
        if len(self.order.items) == 0:
            score = self.compute_score()
            self.level.remove_customer(self, True, score)
        else:
            self.patience_ticks -= 1
            if self.patience_ticks <= 0:
                score = 0 if self.level.alt_suspicion_mode else MAX_SCORE_FROM_CUSTOMER
                self.level.remove_customer(self, False, score)


class Level(pyglet.event.EventDispatcher):

    event_types = (
        'on_customer_arrives',
        'on_customer_leaves',
        'on_level_success',
        'on_level_fail',
    )

    serve_style = 'fast'
    background_scenery = scenery.BackgroundVillage
    device_specification = ()
    #format [arrival_time (seconds since start of level), [order]]
    customer_specification = []
    customer_spaces_specification = 1
    fail_ratio = 1.0
    opening_scene = None
    victory_scene = None
    failure_scene = None
    next_level = None
    alt_suspicion_mode = True
    alt_suspicion_rate = 0.04
    alt_suspicion_time = 60.0

    #seconds
    duration = 60

    #: The duration (in ticks) (computed automatically).
    duration_ticks = None

    def __init__(self):
        '''Construct a `Level` object.

        '''
        self.duration_ticks = int(self.duration // TICK_LENGTH)

        self.entities = []

        self.customers = []
        self.devices = []
        self.items = []
        self.scenery = []
        self.score = 0
        self.tick_running = 0
        self.customer_specification = list(self.customer_specification)
        self.held_item = None
        

        # Create devices.
        self.device_locations = {}
        for device, location_x, location_y in self.device_specification:
            new_device = device(self)
            self.device_locations[new_device] = (location_x, location_y)
            for subdevice in getattr(new_device, 'subdevices', []):
                self.device_locations[subdevice] = (location_x, location_y)

        self.happy_customer = 0
        self.sad_customer = 0

    def add_entity(self, entity):
        self.entities.append(entity)
        if isinstance(entity, Customer):
            self.customers.append(entity)
            self.dispatch_event('on_customer_arrives', entity)
        if isinstance(entity, device.Device):
            self.devices.append(entity)
        if isinstance(entity, item.Item):
            self.items.append(entity)
        if isinstance(entity, scenery.Scenery):
            self.scenery.append(entity)

    def remove_entity(self, entity):
        self.entities.remove(entity)
        if isinstance(entity, Customer):
            self.customers.remove(entity)
            self.dispatch_event('on_customer_leaves', entity)
        if isinstance(entity, device.Device):
            self.devices.remove(entity)
        if isinstance(entity, item.Item):
            self.items.remove(entity)
        if isinstance(entity, scenery.Scenery):
            self.scenery.remove(entity)

    def debug_print(self):
        print(f'level:')
        found_items = []
        for customer in self.customers:
            print(f'  customer: {customer.name}')
            for item in customer.order.items:
                print(f'    item: {item.name}')
                found_items.append(item)
        for device in self.devices:
            print(f'  device: {type(device).__name__}')
            if device.current_item:
                print(f'    item: {device.current_item.name}')
                found_items.append(device.current_item)
        for item in self.items:
            if item not in found_items:
                if item is self.held_item:
                    print(f'  item: {item.name} (held)')
                else:
                    print(f'  item: {item.name}')
        for scenery in self.scenery:
            print(f'  scenery: {scenery.name}')

    def get_device(self, name):
        '''Return the first device with the given name.

        '''
        for device in self.devices:
            if device.name == name:
                return device
        raise ValueError(f'device not found: {name!r}')

    def get_devices(self, name):
        '''Return all devices with the given name.

        '''
        devices = []
        for device in self.devices:
            if device.name == name:
                devices.append(device)
        return devices

    def interact(self, interactable):
        '''Interact with the given object, possibly changing the held item.

        '''
        if isinstance(interactable, device.Device):
            self.held_item = interactable.interact(self.held_item)
        elif isinstance(interactable, Customer):
            self.held_item = interactable.interact(self.held_item)

    def remove_customer(self, customer, success, score):
        '''Remove a customer from level

        '''
        customer.destroy()
        if success == True:
            self.happy_customer += 1
        else:
            self.sad_customer += 1
        if self.alt_suspicion_mode:
            self.score -= score
        else:
            self.score += score

    @property
    def fail_score(self):
        if self.alt_suspicion_mode:
            return self.alt_suspicion_time * self.alt_suspicion_rate * TICK_RATE
        else:
            return int(self.fail_ratio * len(type(self).customer_specification) * MAX_SCORE_FROM_CUSTOMER)

    def get_score_ratio(self):
        return self.score / self.fail_score

    def get_time_ratio(self):
        return self.tick_running / self.duration_ticks

    def has_level_ended(self):
        if self.score >= self.fail_score:
            # we gained to much suspision and have been caught
            self.end_level(False)
            return True
        elif self.tick_running >= self.duration_ticks:
            # we have run out of time
            # any reminaing customers in queue or at counter show score max sus (and we should probably fail?)
            if not self.alt_suspicion_mode:
                self.score += (len(self.customers) + len(self.customer_specification)) * MAX_SCORE_FROM_CUSTOMER
            self.end_level(False)
            return True
        elif len(self.customers) + len(self.customer_specification) == 0:
            # we have severd all the customers and (due to earlier check, not run out of time or scored too much)
            self.end_level(True)
            return True
        else:
            return False

    def end_level(self, success):
        if success is True:
            #end level with success!
            self.dispatch_event('on_level_success')
        else:
            #end level with fail
            self.dispatch_event('on_level_fail')

    
    def tick(self):
        '''Advance the level state by a single tick.

        '''

        self.tick_running += 1
        
        # check if level has ended, we won't be continuing if we have
        if self.has_level_ended():
            return

        for entity in self.entities:
            entity.tick()

        if self.alt_suspicion_mode:
            self.score = max(0.0, self.score + self.alt_suspicion_rate)

        if len(self.customer_specification) > 0 and len(self.customers) < self.customer_spaces_specification:
            # we have the space to spawn a customer, if one is waiting
            # we assume customers are in a queue in the right order!
            time, customer_type, order = self.customer_specification[0]
            if (int(time / TICK_LENGTH) <= self.tick_running):
                order = Order(*[item_class(self) for item_class in order])
                new_customer = Customer(self, order, customer_type)
                self.customer_specification.pop(0)


class TestLevel(Level):

    device_specification = [
        (device.Dough, -0.5, -0.1),
        (device.Cooking, 0.0, -0.1),
        (device.IcingBlue, 0.5, -0.1),
        (device.Bin, -0.8, -0.4),
        (device.MultiPlating, -0.5, -0.3),
        (device.Plate, 0.0, -0.3),
        (device.SprinklesPurple, 0.5, -0.3),
    ]

    customer_specification = [
        (0, 'cop_rabbit', [item.DoughnutUncooked] * 1),
        (50, 'friend_patches', [item.DoughnutUncooked] * 2),
        (100, 'cop_rabbit', [item.DoughnutUncooked] * 3),
        (150, 'friend_patches', [item.DoughnutUncooked] * 3),
    ]

    customer_spaces_specification = 4

    background_scenery = scenery.BackgroundHill

class LevelOne(Level):

    background_scenery = scenery.BackgroundVillage

    opening_scene = 'level_1_opening'
    victory_scene = 'level_1_victory'
    failure_scene = 'level_1_failure'

    serve_style = 'fast'
    fail_ratio = 0.75 
    duration = 33
    alt_suspicion_rate = 0.05
    alt_suspicion_time = 31

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.15),
        (device.Bin, 0.75, -0.4),
    ]

    customer_specification = [
        (2, 'cop_rabbit' ,[item.DoughnutCooked] * 3),
    ]

class LevelOneBee(LevelOne):
    failure_scene = 'level_1B_failure'

class LevelTwo(Level):

    background_scenery = scenery.BackgroundVillage
    customer_spaces_specification = 2

    opening_scene = 'level_2_opening'
    victory_scene = 'level_2_victory'
    failure_scene = 'level_2_failure'

    serve_style = 'fast'
    fail_ratio = 0.4
    duration = 50
    alt_suspicion_rate = 0.05
    alt_suspicion_time = 21

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.15),
        (device.IcingPink, 0.5, -0.05),
        (device.Bin, 0.75, -0.4),
    ]

    customer_specification = [
        (2, 'cop_dog', [item.DoughnutIcedPink]),
        (10, 'slacker_patches', [item.DoughnutUncooked]),
        (15, 'cop_rabbit', [item.DoughnutCooked]),
        (17, 'cop_dog', [item.DoughnutIcedPink]),
    ]

class LevelTwoBee(LevelTwo):
    failure_scene = 'level_2B_failure'

class LevelThree(Level):

    background_scenery = scenery.BackgroundVillage
    customer_spaces_specification = 2

    opening_scene = 'level_3_opening'
    victory_scene = 'level_3_victory'
    failure_scene = 'level_3_failure'

    serve_style = 'fast'
    fail_ratio = 0.55
    duration = 65
    alt_suspicion_rate = 0.04
    alt_suspicion_time = 36

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.15),
        (device.IcingPink, 0.5, -0.05),
        (device.IcingBlue, 0.6, -0.15),
        (device.MultiPlating, 0.0, -0.1),
        (device.Plate, 0.0, -0.29),
        (device.Bin, 0.75, -0.4),
    ]

    customer_specification = [
        (2, 'cop_dog', [item.DoughnutIcedBlue]),
        (8, 'cop_rabbit', [item.DoughnutIcedBlue, item.DoughnutCooked]),
        (12, 'cop_dog', [item.DoughnutIcedPink]),
        (25, 'cop_rabbit', [item.DoughnutIcedPink, item.DoughnutIcedBlue]),
    ]

class LevelThreeBee(LevelThree):
    failure_scene = 'level_3B_failure'

class LevelFour(Level):

    background_scenery = scenery.BackgroundHill
    customer_spaces_specification = 3

    duration = 90

    opening_scene = 'level_4_opening'
    victory_scene = 'level_4_victory'
    failure_scene = 'level_4_failure'

    serve_style = 'fast'
    fail_ratio = 0.8
    alt_suspicion_rate = 0.04
    alt_suspicion_time = 40

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.1),
        (device.Cooking, 0.35, -0.275),
        (device.IcingPink, 0.5, -0.05),
        (device.IcingBlue, 0.6, -0.15),
        (device.MultiPlating, 0.0, -0.1),
        (device.Plate, 0.075, -0.28),
        (device.Bin, 0.75, -0.4),
        (device.SprinklesPurple, -0.25, -0.1),
        (device.SprinklesYellow, -0.2, -0.25),
    ]

    customer_specification = [
        (1, 'cop_elephant', [item.DoughnutFinalBluePurple]),
        (7, 'cop_rabbit', [item.DoughnutCooked, item.DoughnutIcedBlue]),
        (17, 'cop_dog', [item.DoughnutIcedPink]),
        (18, 'cop_rabbit', [item.DoughnutCooked]),
        (25, 'cop_elephant', [item.DoughnutFinalPinkYellow, item.DoughnutFinalPinkPurple, item.DoughnutCooked]),
    ]

class LevelFourBee(LevelFour):
    failure_scene = 'level_4B_failure'

class LevelOneTutorial(Level):

    background_scenery = scenery.BackgroundVillage

    opening_scene = 'tutorial_level_1_opening'
    victory_scene = 'tutorial_level_1_complete'
    failure_scene = 'tutorial_level_1_complete'

    serve_style = 'fast'
    fail_ratio = 1 
    duration = 120

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.15),
        (device.Bin, 0.75, -0.4),
    ]

    customer_specification = [
        (0, 'friend_patches' ,[item.DoughnutCooked]),
    ]

class LevelTwoTutorial(Level):

    background_scenery = scenery.BackgroundVillage

    opening_scene = 'tutorial_level_2_opening'
    victory_scene = 'tutorial_level_2_complete'
    failure_scene = 'tutorial_level_2_complete'

    serve_style = 'fast'
    fail_ratio = 1
    duration = 120

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.15),
        (device.IcingPink, 0.5, -0.05),
        (device.Bin, 0.75, -0.4),
    ]

    customer_specification = [
        (0, 'friend_patches' ,[item.DoughnutIcedPink]),
    ]

class LevelThreeTutorial(Level):

    background_scenery = scenery.BackgroundVillage

    opening_scene = 'tutorial_level_3_opening'
    victory_scene = 'tutorial_level_3_complete'
    failure_scene = 'tutorial_level_3_complete'

    serve_style = 'fast'
    fail_ratio = 1
    duration = 120

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.15),
        (device.IcingBlue, 0.5, -0.05),
        (device.IcingPink, 0.6, -0.15),
        (device.MultiPlating, 0.0, -0.1),
        (device.Plate, 0.0, -0.29),
        (device.Bin, 0.75, -0.4),
    ]

    customer_specification = [
        (0, 'friend_patches' ,[item.DoughnutIcedPink]),
    ]

class LevelFourTutorial(Level):

    background_scenery = scenery.BackgroundHill

    opening_scene = 'tutorial_level_4_opening'
    victory_scene = 'tutorial_level_4_complete'
    failure_scene = 'tutorial_level_4_complete'

    serve_style = 'fast'
    fail_ratio = 1
    duration = 120

    device_specification = [
        (device.Dough, -0.5, -0.2),
        (device.Cooking, 0.25, -0.1),
        (device.Cooking, 0.35, -0.275),
        (device.IcingBlue, 0.5, -0.05),
        (device.IcingPink, 0.6, -0.15),
        (device.MultiPlating, 0.0, -0.1),
        (device.Plate, 0.075, -0.28),
        (device.Bin, 0.75, -0.4),
        (device.SprinklesPurple, -0.25, -0.1),
        (device.SprinklesYellow, -0.2, -0.25),
    ]

    customer_specification = [
        (0, 'friend_patches' ,[item.DoughnutFinalBluePurple]),
    ]


default_level = LevelOne
LevelOne.next_level = LevelTwo
LevelTwo.next_level = LevelThree
LevelThree.next_level = LevelFour
