'''applib.model.devices -- things that convert items

'''


import applib
import pyglet

from applib.constants import TICK_LENGTH
from applib.model import entity
from applib.model import item


class Device(entity.Entity):

    group = 'devices'

    # The time after complete where the contents become ruined - default 0.0, does not ruin
    ruined_time = 0.0

    # The time (in ticks) for the contents of the machine to be ruined (computed automatically).
    ruined_ticks = None

    ruined_item = None

    #: The duration (in seconds) of one cycle of this device.
    duration = 10.0

    #: The duration (in ticks) of one cycle of this device (computed automatically).
    duration_ticks = None

    # input-item, current-item : held-item, new-current-item
    recipes = {}

    alt_sprites = {}

    item_position = (0.0, 0.0)

    default_sound = applib.engine.sound.pop

    _sound_player = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.duration_ticks = int(cls.duration // TICK_LENGTH)
        cls.ruined_ticks = int(cls.ruined_time // TICK_LENGTH)

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

    def compute_transition(self, first_item_class, second_item_class):
        # Case 1: We have a recipe for the input item and current item; use it.
        if (first_item_class, second_item_class) in self.recipes:
            recipe = self.recipes[first_item_class, second_item_class]
            if len(recipe) == 2:
                new_first_item_class, new_second_item_class = recipe
                transition_sound = self.default_sound
            else:
                new_first_item_class, new_second_item_class, transition_sound = recipe
        # Case 2: There was no input item; pick up the current item.
        elif first_item_class is None:
            new_first_item_class, new_second_item_class, transition_sound = second_item_class, None, applib.engine.sound.pop
        # Case 3: Invalid operation; keep the input item (if any).
        else:
            new_first_item_class, new_second_item_class, transition_sound = first_item_class, second_item_class, None
        # Return the results of the transition.
        return new_first_item_class, new_second_item_class, transition_sound

    def add_item(self, input_item):
        
        # Apply the input to the contents of a plate.
        if (input_item is not None) and isinstance(self.current_item, item.Plate) and (self.current_item.holds is not None):
            current_item = self.current_item.holds
            modifying_holds = True
        else:
            current_item = self.current_item
            modifying_holds = False

        # Compute the results of the transition.
        input_item_class = type(input_item) if isinstance(input_item, item.Item) else input_item
        current_item_class = type(current_item) if isinstance(current_item, item.Item) else current_item
        output_item_class, new_item_class, transition_sound = self.compute_transition(input_item_class, current_item_class)

        # Determine which sides of the transition have changed.
        changed_input = not isinstance(input_item, output_item_class or type(None))
        changed_current = not isinstance(current_item, new_item_class or type(None))

        # Trigger sound when anything has changed.
        if changed_input or changed_current:
            if transition_sound is not None:
                if self._sound_player:
                    self._sound_player.next_source()
                if isinstance(transition_sound, tuple):
                    transition_sound = transition_sound[modifying_holds]
                self._sound_player = transition_sound()

        # Trigger timed behaviour when the current item has changed.
        if changed_current:
            # If we changed over time then the device starts a new cycle.
            if input_item_class is item.Time:
                self.ticks_remaining = self.duration_ticks
            # If we added an item then the device needs to be started.
            elif new_item_class is not None:
                self.ticks_remaining = self.duration_ticks
            # If we removed the current item then device needs to be stopped.
            else:
                self.ticks_remaining = None

        # Check for special plate behaviour.
        if current_item_class is new_item_class is item.Plate:
            if (current_item.holds is None) and (output_item_class is None):
                current_item.holds = input_item

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
        elif (new_item_class is current_item_class) and (output_item is not current_item):
            new_item = current_item
        else:
            new_item = new_item_class(self.level)

        # Make sure that unused items are destroyed.
        remaining_items = []
        for root_item in (output_item, new_item):
            if isinstance(root_item, item.Item):
                remaining_items.append(root_item)
                if isinstance(root_item.holds, item.Item):
                    remaining_items.append(root_item.holds)
        if input_item not in remaining_items:
            if isinstance(input_item, item.Item):
                input_item.destroy()
        if current_item not in remaining_items:
            if isinstance(current_item, item.Item):
                current_item.destroy()

        # Store the new item and return the output item.
        if modifying_holds:
            self.current_item.holds = new_item
        else:
            self.current_item = new_item
        return output_item

    def interact(self, held_item):
        return self.add_item(held_item)

    def tick(self):
        super().tick()
        if self.ticks_remaining is not None:
            self.ticks_remaining -= 1
            if self.ticks_remaining == 0:
                self.add_item(item.Time)
        if self.ticks_remaining is not None:
            if self.ticks_remaining <= -self.ruined_ticks < 0:
                self.add_item(item.Time)
                self.ticks_remaining = None



class AutomaticDevice(Device):

    product = None

    duration = 0.0

    sound = None

    def add_item(self, input_item):
        # Bins simply consume the input item.
        if self.product is None:
            self.ticks_remaining = self.duration_ticks
            if input_item is not None:
                if self.sound is not None:
                    self.sound()
                input_item.destroy()
            return None
        # Non-bins give you their product if you aren't hold anything
        elif input_item is None:
            if self.sound is not None:
                self.sound()
            self.ticks_remaining = self.duration_ticks
            return self.product(self.level)
        # Otherwise you keep what you are holding.
        else:
            return input_item


## Actual Devices

class Bin(AutomaticDevice):
    
    name = 'station_bin'

    product = None

    sound = applib.engine.sound.throw_away


class Plate(AutomaticDevice):

    name = 'station_plate'

    product = item.Plate

    sound = applib.engine.sound.plate_pickup

class Plating(Device):

    name = 'station_none'

    duration = 0.0

    recipes = {
        (item.Plate, None): (None, item.Plate, applib.engine.sound.plate_putdown),
        (item.DoughnutUncooked, item.Plate): (None, item.Plate),
        (item.DoughnutCooked, item.Plate): (None, item.Plate),
        (item.DoughnutIcedBlue, item.Plate): (None, item.Plate),
        (item.DoughnutIcedPink, item.Plate): (None, item.Plate),
        (item.DoughnutFinalBluePurple, item.Plate): (None, item.Plate),
        (item.DoughnutFinalBlueYellow, item.Plate): (None, item.Plate),
        (item.DoughnutFinalPinkPurple, item.Plate): (None, item.Plate),
        (item.DoughnutFinalPinkYellow, item.Plate): (None, item.Plate),
        (item.LadlePurple, item.DoughnutIcedBlue): (None, item.DoughnutFinalBluePurple, (applib.engine.sound.sprinkle_board, applib.engine.sound.sprinkle_plate)),
        (item.LadlePurple, item.DoughnutIcedPink): (None, item.DoughnutFinalPinkPurple, (applib.engine.sound.sprinkle_board, applib.engine.sound.sprinkle_plate)),
        (item.LadleYellow, item.DoughnutIcedBlue): (None, item.DoughnutFinalBlueYellow, (applib.engine.sound.sprinkle_board, applib.engine.sound.sprinkle_plate)),
        (item.LadleYellow, item.DoughnutIcedPink): (None, item.DoughnutFinalPinkYellow, (applib.engine.sound.sprinkle_board, applib.engine.sound.sprinkle_plate)),
        (None, item.Plate): (item.Plate, None, applib.engine.sound.plate_pickup),
    }

def _populate_plating_recipes():
    for item_name, item_class in entity.Entity.index['items'].items():
        if item_name.startswith('doughnut_'):
            Plating.recipes[item_class, None] = (None, item_class)

_populate_plating_recipes()
del _populate_plating_recipes

class MultiPlating(Device):

    name = 'station_plating'

    duration = 0.0

    subpositions = [
        (0.0, -0.15),
        (0.0, 0.2),
    ]

    # subpositions = [
    #     (0.0, 0.2),
    #     (-0.32, -0.15),
    #     (0.3, -0.15),
    # ]

    # subpositions = [
    #     (-0.25, 0.2),
    #     (-0.32, -0.15),
    #     (0.25, 0.2),
    #     (0.3, -0.15),
    # ]

    def __init__(self, *args):
        super().__init__(*args)
        self.subdevices = []
        for x, y in self.subpositions:
            self.subdevices.append(Plating(self.level))
            self.subdevices[-1].item_position = (x, y)
        

    def destroy(self):
        super().destroy()
        for device in self.subdevices:
            device.destroy()


class MultiPlatingRight(MultiPlating):
    
    name = 'station_plating_right'

class MultiPlatingLeft(MultiPlating):

    name = 'station_plating_left'


class Dough(AutomaticDevice):

    name = 'station_dough'

    product = item.DoughnutUncooked

    sound = applib.engine.sound.pop


class Cooking(Device):

    name = 'station_cooking'

    duration = 5.0

    ruined_time = 5.0

    item_position = (0.0, 0.10)

    alt_sprites = {
        item.DoughnutUncooked: ('devices/station_cooking_uncooked.png',),
        item.DoughnutCooked: ('devices/station_cooking_cooked.png',),
        item.DoughnutBurned: (
            'devices/station_cooking_burned1.png',
            'devices/station_cooking_burned2.png',
        ),
    }
    
    recipes = {
        (item.DoughnutUncooked, None): (None, item.DoughnutUncooked, applib.engine.sound.deep_fry),
        (item.Time, item.DoughnutUncooked): (None, item.DoughnutCooked, None),
        (None, item.DoughnutCooked): (item.DoughnutCooked, None),
        (item.Time, item.DoughnutCooked): (None, item.DoughnutBurned, applib.engine.sound.fire_start),
    }

    #sound = applib.engine.sound.deep_fry


class IcingBlue(Device):

    name = 'station_icing_blue'

    duration = 3.0

    item_position = (0.15, -0.3)
    
    recipes = {
        (item.DoughnutCooked, None): (None, item.DoughnutCooked, applib.engine.sound.whirr),
        (item.Time, item.DoughnutCooked): (None, item.DoughnutIcedBlue, applib.engine.sound.squirt),
        (None, item.DoughnutIcedBlue): (item.DoughnutIcedBlue, None),
    }


class IcingPink(Device):

    name = 'station_icing_pink'

    duration = 2.0

    item_position = (0.15, -0.3)
    
    recipes = {
        (item.DoughnutCooked, None): (None, item.DoughnutCooked, applib.engine.sound.whirr),
        (item.Time, item.DoughnutCooked): (None, item.DoughnutIcedPink, applib.engine.sound.squirt),
        (None, item.DoughnutIcedPink): (item.DoughnutIcedPink, None),
    }


class SprinklesPurple(AutomaticDevice):

    name = 'station_sprinkles_purple'

    product = item.LadlePurple

    sound = applib.engine.sound.sprinkle_scoop


class SprinklesYellow(AutomaticDevice):

    name = 'station_sprinkles_yellow'

    product = item.LadleYellow

    sound = applib.engine.sound.sprinkle_scoop
