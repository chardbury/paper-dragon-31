'''applib.model.devices -- things that convert items

'''


import applib
import pyglet

from applib.constants import TICK_LENGTH
from applib.model import entity
from applib.model import item


class Device(entity.Entity):

    group = 'devices'

    # The time after complete where the contents become ruined - default None, does not ruin
    ruined_time = None
    ruined_item = None

    #: The duration (in seconds) of one cycle of this device.
    duration = 1.0

    #: The duration (in ticks) of one cycle of this device (computed automatically).
    duration_ticks = None

    # input-item, current-item : held-item, new-current-item
    recipes = {}

    item_position = (0.0, 0.0)

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.duration_ticks = int(cls.duration // TICK_LENGTH)

    def __init__(self, level):
        super().__init__(level)
        self.current_item = None
        self.ticks_remaining = None

    @property
    def is_running(self):
        return (self.ticks_remaining is not None) and (self.ticks_remaining > 0)

    @property
    def is_finished(self):
        return (self.ticks_remaining is not None) and (self.ticks_remaining <= 0)

    @property
    def is_ruined(self):
        return (self.ruined_time is not None) and (self.ticks_remaining is not None) and (self.ticks_remaining <= 0) and (-(self.ruined_time // TICK_LENGTH) > self.ticks_remaining)

    def compute_transition(self, first_item_class, second_item_class):
        # Case 1: Device has ruined current content, if we are holding nothing we return this
        if self.is_ruined and first_item_class is None:
            new_first_item_class, new_second_item_class = self.ruined_item, None
        # Case 2: We have a recipe for the input item and current item; use it.
        elif (first_item_class, second_item_class) in self.recipes:
            new_first_item_class, new_second_item_class = self.recipes[first_item_class, second_item_class]
        # Case 3: There was no input item; pick up the current item.
        elif first_item_class is None:
            new_first_item_class, new_second_item_class = second_item_class, None
        # Case 4: Invalid operation; keep the input item (if any).
        else:
            new_first_item_class, new_second_item_class = first_item_class, second_item_class
        # Return the results of the transition.
        return new_first_item_class, new_second_item_class

    def add_item(self, input_item):
        current_item = self.current_item

        # Compute the results of the transition.
        input_item_class = type(input_item) if isinstance(input_item, item.Item) else input_item
        current_item_class = type(current_item) if isinstance(current_item, item.Item) else current_item
        output_item_class, new_item_class = self.compute_transition(input_item_class, current_item_class)

        # Determine which sides of the transition have changed.
        changed_input = not isinstance(input_item, output_item_class or type(None))
        changed_current = not isinstance(current_item, new_item_class or type(None))

        # Trigger things when items have changed.
        if changed_current:
            # If we added an item then the device needs to be started.
            if new_item_class is not None:
                self.ticks_remaining = self.duration_ticks
            # If we removed the current item then device needs to be stopped.
            else:
                self.ticks_remaining = None

        # Work out where the output item came from.
        if output_item_class is None:
            output_item = None
        elif output_item_class is input_item_class:
            output_item = input_item
        elif output_item_class is current_item_class:
            output_item = current_item
        else:
            output_item = output_item_class(self.level)

        # Work out where the new item came from.
        if new_item_class is None:
            new_item = None
        elif (new_item_class is input_item_class) and (output_item is not input_item):
            new_item = input_item
        elif (output_item_class is current_item_class) and (output_item is not current_item):
            new_item = current_item
        else:
            new_item = new_item_class(self.level)

        # Make sure that unused items are destroyed.
        if input_item not in (output_item, new_item):
            input_item.destroy()
        if current_item not in (output_item, new_item):
            current_item.destroy()

        # Store the new item and return the output item.
        self.current_item = new_item
        return output_item

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
            if input_item is not None:
                input_item.destroy()
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
    
    name ='station_bin'

    product = None


class Plate(Device):

    name = 'station_plate'

    duration = 0.0

    recipes = {
        (item.Sprinkles, item.DoughnutGlazed): (None, item.DoughnutSprinkles),
    }

def _populate_plate_recipes():
    for item_name, item_class in entity.Entity.index['items'].items():
        Plate.recipes[item_class, None] = (None, item_class)

_populate_plate_recipes()
del _populate_plate_recipes


class Dough(AutomaticDevice):

    name = 'station_dough'

    product = item.DoughnutUncooked


class Cooking(Device):

    name = 'station_cooking'

    ruined_time = 10
    ruined_item = item.DoughnutBurned

    item_position = (0.0, 0.10)
    
    recipes = {
        (item.DoughnutUncooked, None): (None, item.DoughnutUncooked),
        (None, item.DoughnutUncooked): (item.DoughnutCooked, None),
    }


class Icing(Device):

    name = 'station_icing'

    item_position = (0.15, -0.3)
    
    recipes = {
        (item.DoughnutCooked, None): (None, item.DoughnutCooked),
        (None, item.DoughnutCooked): (item.DoughnutGlazed, None),
    }


class Sprinkles(AutomaticDevice):

    name = 'station_sprinkles'

    product = item.Sprinkles
