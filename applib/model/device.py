'''applib.model.devices -- things that convert items

'''


import applib
import pyglet

from applib.constants import TICK_LENGTH
from applib.model import entity
from applib.model import item


class Device(entity.Entity):

    group = 'devices'

    #: The duration (in seconds) of one cycle of this device.
    duration = 10.0

    #: The duration (in ticks) of one cycle of this device (computed automatically).
    duration_ticks = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.duration_ticks = int(cls.duration // TICK_LENGTH)

    def __init__(self, level):
        super().__init__(level)
        self.current_input = None
        self.ticks_remaining = None

    @property
    def is_running(self):
        return self.ticks_remaining is not None

    @property
    def is_finished(self):
        return self.is_running and (self.ticks_remaining <= 0.0)

    def get_output_item(self, input_item):
        pass

    def add_item(self, input_item):
        output_item = self.get_output_item(input_item)
        if output_item is not None:
            self.current_input = input_item
            self.ticks_remaining = self.duration_ticks

    def remove_item(self):
        output_item = self.get_output_item(self.current_input)
        self.current_input = None
        self.ticks_remaining = None
        return output_item(self.level)

    def interact(self, held_item):
        if self.is_running:
            if held_item is None:
                if self.is_finished:
                    return self.remove_item()
            else:
                return held_item
        else:
            self.add_item(held_item)
            if not self.is_running:
                return held_item

    def tick(self):
        super().tick()
        if self.ticks_remaining is not None:
            self.ticks_remaining -= 1


class AutomaticDevice(Device):

    product = None

    duration = 0

    def __init__(self, level):
        super().__init__(level)
        self.ticks_remaining = self.duration

    def remove_item(self):
        self.ticks_remaining = self.duration
        return self.product(self.level)


## Actual Devices

class TestApricot(Device):
    name = 'apricot'

class TestLilac(Device):
    name = 'lilac'

class TestMint(Device):
    name = 'mint'



class BatterBox(AutomaticDevice):

    name = 'batter_box'

    product = item.Batter


class DoughnutImprover(Device):

    name = 'doughnut_improver'
    
    def get_output_item(self, input_item):
        if isinstance(input_item, item.Doughnut):
            return item.BetterDoughnut
