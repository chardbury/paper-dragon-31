'''applib.model.level -- self-contained game level

'''

import random

import applib
import pyglet

from applib.constants import TICK_LENGTH
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
            if match_item.holds and item.matches(match_item.holds):
                self.items.pop(index).destroy()
                return True
        return False


class Customer(entity.Entity):

    group = 'customers'

    start_patience = 30

    customer_images = [
        'cop_dog',
        'cop_elephant',
        'cop_rabbit',
        'friend_patches',
    ]

    def __init__(self, level, order):
        self.name = random.choice(self.customer_images)
        super().__init__(level)
        self.order = order
        self.patience = self.compute_patience()

    def destroy(self):
        super().destroy()
        for item in self.order.items:
            item.destroy()

    def compute_patience(self):
        '''Return the patience in ticks

        '''
        return int(self.start_patience // TICK_LENGTH)

    def get_patience_ratio(self):
        return (self.patience / (self.start_patience // TICK_LENGTH))

    def interact(self, held_item):
        if self.order.remove(held_item):
            held_item.destroy()
        else:
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
    
    def compute_score_fast(self):
        percentage_remaining_patience = self.get_patience_ratio() * 100
        if percentage_remaining_patience >= 80:
            return 0
        elif percentage_remaining_patience >= 40:
            return MAX_SCORE_FROM_CUSTOMER * 0.125
        elif percentage_remaining_patience >= 20:
            return MAX_SCORE_FROM_CUSTOMER * 0.25
        elif percentage_remaining_patience >= 5:
            return MAX_SCORE_FROM_CUSTOMER * 0.5
        else:
            return MAX_SCORE_FROM_CUSTOMER * 0.75

    def compute_score_slow(self):
        percentage_remaining_patience = self.get_patience_ratio() * 100
        if percentage_remaining_patience >= 80:
            return MAX_SCORE_FROM_CUSTOMER * 0.75
        elif percentage_remaining_patience >= 40:
            return MAX_SCORE_FROM_CUSTOMER * 0.5
        elif percentage_remaining_patience >= 20:
            return MAX_SCORE_FROM_CUSTOMER * 0.25
        elif percentage_remaining_patience >= 5:
            return MAX_SCORE_FROM_CUSTOMER * 0.125
        else:
            return 0

    def tick(self):
        if len(self.order.items) == 0:
            if self.level.serve_style == 'slow':
                score = self.compute_score_slow()
            elif self.level.serve_style == 'fast':
                score = self.compute_score_fast()
            else:
                raise ValueError
            self.level.remove_customer(self, True, score)
        else:
            self.patience -= 1
            if self.patience <= 0:
                self.level.remove_customer(self, False, MAX_SCORE_FROM_CUSTOMER)


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
            print(f'  device: {device.name}')
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
        self.score += score

    @property
    def fail_score(self):
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
            pass

        if len(self.customer_specification) > 0 and len(self.customers) < self.customer_spaces_specification:
            # we have the space to spawn a customer, if one is waiting
            # we assume customers are in a queue in the right order!
            time, order = self.customer_specification[0]
            if (int(time / TICK_LENGTH) <= self.tick_running):
                order = Order(*[item_class(self) for item_class in order])
                new_customer = Customer(self, order)
                self.customer_specification.pop(0)

        for entity in self.entities:
            entity.tick()


class TestLevel(Level):

    device_specification = [
        (device.Dough, -0.5, -0.1),
        (device.Cooking, 0.0, -0.1),
        (device.IcingBlue, 0.5, -0.1),
        (device.Bin, -0.8, -0.4),
        (device.Plating, -0.5, -0.3),
        (device.Plate, 0.0, -0.3),
        (device.SprinklesPurple, 0.5, -0.3),
    ]

    customer_specification = [
        (0, [item.DoughnutUncooked] * 1),
        (5, [item.DoughnutCooked] * 2),
        (10, [item.DoughnutIcedBlue] * 3),
        (15, [item.DoughnutFinalBluePurple] * 3),
    ]


class LevelOne(Level):

    opening_scene = 'level_1_opening'
    victory_scene = 'level_1_victory'
    failure_scene = 'level_1_failure'

    serve_style = 'fast'
    fail_ratio = 0.5 

    background_scenery = scenery.BackgroundVillage

    device_specification = [
        (device.Dough, -0.5, -0.1),
        (device.Cooking, 0.0, -0.1),
        (device.Bin, -0.5, -0.3),
    ]

    customer_specification = [
        (2, [item.DoughnutCooked, item.DoughnutCooked, item.DoughnutCooked]),
    ]


class LevelTwo(Level):

    opening_scene = 'level_2_opening'
    victory_scene = 'level_2_victory'
    failure_scene = 'level_2_failure'

    serve_style = 'fast'
    fail_ratio = 0.5

    device_specification = [
        (device.Dough, -0.5, -0.1),
        (device.Cooking, 0.0, -0.1),
        (device.IcingBlue, 0.5, -0.1),
        (device.Bin, -0.5, -0.3),
    ]

    customer_specification = [
        (2, [item.DoughnutIcedBlue]),
    ]

class LevelThree(Level):

    opening_scene = 'level_3_opening'
    victory_scene = 'level_3_victory'
    failure_scene = 'level_3_failure'

    serve_style = 'fast'
    fail_ratio = 0.5

    device_specification = [
        (device.Dough, -0.5, -0.1),
        (device.Cooking, 0.0, -0.1),
        (device.IcingBlue, 0.5, -0.1),
        (device.Bin, -0.5, -0.3),
    ]

    customer_specification = [
        (2, [item.DoughnutIcedBlue]),
    ]

class LevelFour(Level):

    opening_scene = 'level_4_opening'
    victory_scene = 'level_4_victory'
    failure_scene = 'level_4_failure'

    serve_style = 'fast'
    fail_ratio = 0.5

    device_specification = [
        (device.Dough, -0.5, -0.1),
        (device.Cooking, 0.0, -0.1),
        (device.IcingBlue, 0.5, -0.1),
        (device.Bin, -0.5, -0.3),
    ]

    customer_specification = [
        (2, [item.DoughnutIcedBlue]),
    ]

LevelOne.next_level = LevelTwo
LevelTwo.next_level = LevelThree
LevelThree.next_level = LevelFour
