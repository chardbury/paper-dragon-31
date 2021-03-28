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
        self.held_item = None
        self.devices = [
            device.BatterBox(),
            device.DoughnutImprover(),
        ]
        self.customers = []

    def get_devices(self, name):
        return [device for device in self.devices if device.name == name]

    def interact(self, device):
        self.held_item = device.interact(self.held_item)
    
    def tick(self):
        for device in self.devices:
            device.tick()
        for customer in self.customers:
            customer.tick()
