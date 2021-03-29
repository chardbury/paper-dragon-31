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

     # input-item, current-item : held-item, new-current-item
    recipes = {}

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
        lookup = type(input_item), type(self.current_input)
        if lookup in self.recipes:
            return self.recipes[lookup]
        elif input_item is None:
            return (type(self.current_input), type(None))
        else:
            return (type(input_item), type(None))

    def add_item(self, input_item):
        # returns held-item class and new current-item class
        out, current = self.get_output_item(input_item)
        
        changed = out is not type(input_item) or current is not type(self.current_input)
        self.current_input = current(self.level) if (current is not type(None)) else None

        if changed:
            # if we added something and device not running then we need to start it
            if current is not type(None):
                self.ticks_remaining = self.duration_ticks
            # if we removed the current item then device needs to be stopped
            else:
                self.ticks_remaining = None
        
        # set current item and return output item        
        return out(self.level) if (out is not type(None)) else None

    def interact(self, held_item):
        if not self.is_running or self.is_finished:
            return self.add_item(held_item)
        else:
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

    def add_item(self, held_item):
        self.ticks_remaining = self.duration
        return self.product(self.level)


## Actual Devices

class Plate(Device):

    name = 'plate'

    duration = 0

    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Glaze, item.Doughnut): (type(None), item.DoughnutGlazed),
        (item.Sprinkles, item.Doughnut): (type(None), item.DoughnutSprinkles),
        (item.Doughnut, type(None)): (type(None), item.Doughnut),
        }


class TestApricot(AutomaticDevice):

    name = 'apricot'

    product = item.Batter


class TestLilac(Device):

    name = 'lilac'

    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Batter, type(None)): (type(None), item.Batter),
        (type(None), item.Batter): (item.Doughnut, type(None)),
        }

class TestMint(Device):

    name = 'mint'

    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Doughnut, type(None)): (type(None), item.Doughnut),
        (type(None), item.Doughnut): (item.DoughnutCooked, type(None)),
        }


class BatterTray(AutomaticDevice):

    name = 'batter_tray'

    product = item.Batter

class DoughnutFryer(Device):

    name = 'doughnut_fryer'
    
    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Batter, type(None)): (type(None), item.Batter),
        (type(None), item.Batter): (item.Doughnut, type(None)),
        }
