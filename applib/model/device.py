'''applib.model.devices -- things that convert items

'''


import applib
import pyglet

from applib.constants import TICK_LENGTH
from applib.model import item


def _normalize(string):
    string = string.strip().lower()
    string = re.sub(r'\s+', '_', string)
    string = re.sub(r'[^a-z_]', '', string)
    return string


class Device(object):

    name = None

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


## Actual Devices


class BatterBox(AutomaticDevice):

    name = 'batter_box'

    product = item.Item.get('batter')


class DoughnutImprover(Device):

    name = 'doughnut_improver'
    
    def get_output_item(self, input_item):
        if input_item == item.get('doughnut'):
            return item.get('better_doughnut')
