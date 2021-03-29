'''applib.model.level -- self-contained game level

'''

import random

import applib

from applib.constants import TICK_LENGTH
from applib.model import item
from applib.model import device


class Order(object):

    def __init__(self, *items):
        self.items = list(items)


class Customer(object):

    def __init__(self, order, level):
        self.order = order
        self.patience = self.compute_patience()
        self.level = level

    def compute_patience(self):
        '''Return the patience in ticks

        '''
        return int(random.randint(10, 30) // TICK_LENGTH)

    def interact(self, held_item):
        if held_item in self.order.items:
            self.order.items.remove(held_item)
        else:
            return held_item

    def tick(self):
        if len(self.order.items) == 0:
            self.level.remove_customer(self, True)
        self.patience -= 1
        if (self.patience <= 0):
            self.level.remove_customer(self, False)
    


class Level(object):

    device_specification = ()

    def __init__(self):
        '''Construct a `Level` object.

        '''
        self.held_item = None

        # Create devices.
        self.devices = []
        self.device_locations = {}
        for device, location_x, location_y in self.device_specification:
            new_device = device()
            self.devices.append(new_device)
            self.device_locations[new_device] = (location_x, location_y)

        self.customers = []
        self.happy_customer = 0
        self.sad_customer = 0

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


    def add_customer(self, customer):
        '''Add a customer to the level

        '''
        self.customers.append(customer)

    def remove_customer(self, customer, success):
        '''Remove a customer from level

        '''
        self.customers.remove(customer)
        if success == True:
            self.happy_customer += 1
        else:
            self.sad_customer += 1

    
    def tick(self):
        '''Advance the level state by a single tick.

        '''
        if (len(self.customers) == 0):
            self.add_customer(Customer(Order(item.get('doughnut')), self))
        for device in self.devices:
            device.tick()
        for customer in self.customers:
            customer.tick()


class TestLevel(Level):

    device_specification = [
        (device.TestApricot, -0.5, -0.25),
        (device.TestLilac, 0.0, -0.25),
        (device.TestMint, 0.5, -0.25),
    ]
