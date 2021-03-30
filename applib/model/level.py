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
        return int(random.randint(10, 30) // TICK_LENGTH)

    def interact(self, held_item):
        if held_item in self.order.items:
            self.order.items.remove(held_item)
            held_item.destroy()
        else:
            return held_item

    def tick(self):
        if len(self.order.items) == 0:
            self.level.remove_customer(self, True)
        else:
            self.patience -= 1
            if self.patience <= 0:
                self.level.remove_customer(self, False)
    


class Level(object):

    device_specification = ()

    def __init__(self):
        '''Construct a `Level` object.

        '''

        self.entities = []

        self.customers = []
        self.devices = []
        self.items = []
        self.scenery = []

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

    def remove_customer(self, customer, success):
        '''Remove a customer from level

        '''
        customer.destroy()
        if success == True:
            self.happy_customer += 1
        else:
            self.sad_customer += 1

    
    def tick(self):
        '''Advance the level state by a single tick.

        '''
        if len(self.customers) == 0:
            customer = Customer(self, Order(item.Doughnut(self)))
            customer = Customer(self, Order(item.Doughnut(self)))
            customer = Customer(self, Order(item.Doughnut(self)))
            customer = Customer(self, Order(item.Doughnut(self)))
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
