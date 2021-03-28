'''applib.model.level -- self-contained game level

'''

import applib

from applib.constants import TICK_LENGTH
from applib.model import item
from applib.model import device


class Order(object):

    def __init__(self, *items):
        self.items = list(items)


class Customer(object):

    def __init__(self, order):
        self.order = order

    def tick(self):
        pass


class Level(object):

    def __init__(self):
        '''Construct a `Level` object.

        '''
        self.held_item = None
        self.devices = [
            device.BatterBox(),
            device.DoughnutImprover(),
        ]
        self.customers = []

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

    def interact(self, device):
        '''Interact with the given device, possibly changing the held item.

        '''
        self.held_item = device.interact(self.held_item)
    
    def tick(self):
        '''Advance the level state by a single tick.

        '''
        for device in self.devices:
            device.tick()
        for customer in self.customers:
            customer.tick()
