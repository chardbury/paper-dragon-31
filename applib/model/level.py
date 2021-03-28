'''applib.model.level -- self-contained game level

'''

import applib

from applib.constants import TICK_LENGTH


class Item(object):

    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

batter = Item('batter')
doughnut = Item('doughnut')
better_doughnut = Item('better doughnut')


class Order(object):

    def __init__(self, *items):
        self.items = list(items)


class Customer(object):

    def __init__(self, order):
        self.order = order

    def tick(self):
        pass


class Device(object):

    duration = 10.0

    def __init__(self):
        self.current_input = None
        self.time_remaining = None

    @property
    def is_running(self):
        return self.time_remaining is not None

    @property
    def is_finished(self):
        return self.is_running and (self.time_remaining <= 0.0)

    def get_output_item(self, input_item):
        pass

    def add_item(self, input_item):
        output_item = self.get_output_item(input_item)
        if output_item is not None:
            self.current_input = input_item
            self.time_remaining = self.duration

    def remove_item(self):
        output_item = self.get_output_item(input_item)
        self.current_input = None
        self.time_remaining = None
        return output_item

    def interact(self, held_item):
        if self.is_running:
            if held_item is None and self.is_finished:
                return self.remove_item()
        else:
            self.add_item(held_item)
            if not self.is_running:
                return held_item

    def tick(self):
        if self.time_remaining is not None:
            self.time_remaining -= TICK_LENGTH


class AutomaticDevice(Device):

    product = None

    def __init__(self):
        super().__init__()
        self.time_remaining = self.duration

    def remove_item(self):
        self.time_remaining = self.duration
        return self.product


class BatterBox(AutomaticDevice):

    product = batter


class DoughnutImprover(Device):
    
    def get_output_item(self, input_item):
        if input_item == 'doughnut':
            return better_doughnut


class Level(object):

    def __init__(self):
        self.held_item = None
        self.devices = [BatterBox(), DoughnutImprover()]
        self.customers = []

    def interact(self, device):
        self.held_item = device.interact(self.held_item)
    
    def tick(self):
        for device in self.devices:
            device.tick()
        for customer in self.customers:
            customer.tick()


Customer(
    order = Order(
        doughnut,
        doughnut,
    )
)
