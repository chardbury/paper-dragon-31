'''applib.model.level -- self-contained game level

'''

import random

import applib
import pyglet

from applib.constants import TICK_LENGTH
from applib.model import device
from applib.model import entity
from applib.model import item
from applib.model import scenery


class Order(object):

    def __init__(self, *items):
        self.items = list(items)


class Customer(entity.Entity):

    group = 'customers'
    start_patience = 30

    customer_images = [
        'customers/cop_dog.png',
        'customers/cop_elephant.png',
        'customers/cop_rabbit.png',
        'customers/friend_sprinkles.png',
        # 'customers/edgy_customer.png',
    ]

    def __init__(self, level, order):
        self.texture = pyglet.resource.texture(random.choice(self.customer_images))
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

    def interact(self, held_item):
        if held_item in self.order.items:
            self.order.items.remove(held_item)
            held_item.destroy()
        else:
            return held_item
    
    def compute_score(self):
        percentage_remaining_patience = (self.patience / self.start_patience) * 100
        if percentage_remaining_patience >= 80:
            return 0
        elif percentage_remaining_patience >= 40:
            return 5
        elif percentage_remaining_patience >= 20:
            return 10
        elif percentage_remaining_patience >= 5:
            return 20
        else:
            return 30

    def tick(self):
        if len(self.order.items) == 0:
            self.level.remove_customer(self, True, self.compute_score())
        else:
            self.patience -= 1
            if self.patience <= 0:
                self.level.remove_customer(self, False, 40)
    


class Level(pyglet.event.EventDispatcher):

    event_types = (
        'on_customer_arrives',
        'on_customer_leaves',
    )

    device_specification = ()
    #format [arrival_time (seconds since start of level), [order]]
    customer_specification = []
    customer_spaces_specification = 1
    scoring = ()
    
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
            self.devices.append(new_device)
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

    def get_device(self, name):
        '''Return the first device with the given name.

        '''
        for device in self.devices:
            if device.name == name:
                return device

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

    
    def tick(self):
        '''Advance the level state by a single tick.

        '''
        self.tick_running += 1
        if (self.tick_running >= self.duration_ticks):
            # end the level
            # any reminaing customers in queue or at counter show score max sus 
            pass

        if len(self.customer_specification) > 0 and len(self.customers) < self.customer_spaces_specification:
            # we have the space to spawn a customer, if one is waiting
            # we assume customers are in a queue in the right order!
            time, order = self.customer_specification[0]
            if (int(time // TICK_LENGTH) <= self.tick_running):
                order = Order(*[item_class(self) for item_class in order])
                new_customer = Customer(self, order)
                self.customer_specification.pop(0)

        for entity in self.entities:
            entity.tick()


class TestLevel(Level):

    device_specification = [
        (device.TestApricot, -0.5, -0.25),
        (device.TestLilac, 0.0, -0.25),
        (device.TestMint, 0.5, -0.25),
        (device.Bin, -0.25, -0.4),
        (device.Plate, 0.25, -0.4),
    ]

    customer_specification = [
        (0, [item.Batter]),
        (1, [item.Doughnut]),
        (2, [item.DoughnutCooked]),
        (3, [item.DoughnutGlazed]),
    ]
