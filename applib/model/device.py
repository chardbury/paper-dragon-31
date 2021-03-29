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
        return (self.ticks_remaining is not None) and (self.ticks_remaining > 0)

    @property
    def is_finished(self):
        return (self.ticks_remaining is not None) and (self.ticks_remaining <= 0)

    def compute_transition(self, first_item, second_item):
        # Get the classes for the input item and the current item, dealing with missing items.
        first_item_class = type(first_item) if isinstance(first_item, item.Item) else first_item
        second_item_class = type(second_item) if isinstance(second_item, item.Item) else second_item
        # Case 1: We have a recipe for the input item and current item; use it.
        if (first_item_class, second_item_class) in self.recipes:
            new_first_item_class, new_second_item_class = self.recipes[first_item_class, second_item_class]
        # Case 2: There was no input item; pick up the current item.
        elif first_item_class is None:
            new_first_item_class, new_second_item_class = second_item_class, None
        # Case 3: Invalid operation; keep the input item (if any).
        else:
            new_first_item_class, new_second_item_class = first_item_class, None
        # Return the results of the transition.
        return new_first_item_class, new_second_item_class

    def add_item(self, input_item):
        # Compute the results of the transition.
        output_item_class, new_item_class = self.compute_transition(input_item, self.current_input)
        # Determine which sides of the transition have changed.
        changed_input = not isinstance(input_item, output_item_class or type(None))
        changed_current = not isinstance(self.current_input, new_item_class or type(None))
        # Trigger things when items have changed.
        if changed_current:
            # If we added an item then the device needs to be started.
            if new_item_class is not None:
                self.ticks_remaining = self.duration_ticks
            # If we removed the current item then device needs to be stopped.
            else:
                self.ticks_remaining = None
        # Set current item and return the output item.
        self.current_input = new_item_class(self.level) if (new_item_class is not None) else None
        return output_item_class(self.level) if (output_item_class is not None) else None

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

    duration = 0.0

    def add_item(self, input_item):
        # Bins simply consume the input item.
        if self.product is None:
            self.ticks_remaining = self.duration_ticks
            return None
        # Non-bins give you their product if you aren't hold anything
        elif input_item is None:
            self.ticks_remaining = self.duration_ticks
            return self.product(self.level)
        # Otherwise you keep what you are holding.
        else:
            return input_item


## Actual Devices

class Bin(AutomaticDevice):
    
    name ='bin'

    product = None


class Plate(Device):

    name = 'plate'

    duration = 0

    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Glaze, item.Doughnut): (None, item.DoughnutGlazed),
        (item.Sprinkles, item.Doughnut): (None, item.DoughnutSprinkles),
        (item.Doughnut, None): (None, item.Doughnut),
    }


class TestApricot(AutomaticDevice):

    name = 'apricot'

    product = item.Batter


class TestLilac(Device):

    name = 'lilac'

    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Batter, None): (None, item.Batter),
        (None, item.Batter): (item.Doughnut, None),
    }

class TestMint(Device):

    name = 'mint'

    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Doughnut, None): (None, item.Doughnut),
        (None, item.Doughnut): (item.DoughnutCooked, None),
    }


class BatterTray(AutomaticDevice):

    name = 'batter_tray'

    product = item.Batter


class DoughnutFryer(Device):

    name = 'doughnut_fryer'
    
    # input-item, current-item : held-item, new-current-item
    recipes = {
        (item.Batter, None): (None, item.Batter),
        (None, item.Batter): (item.Doughnut, None),
    }
