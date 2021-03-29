'''applib.model.item -- movable items

'''

import re

import applib
import pyglet

from applib.model import entity


class Item(entity.Entity):

    group = 'items'

    def __eq__(self, other):
        return type(self) == type(other)
    
    def __hash__(self):
        return hash(type(self))

class Batter(Item):

    name = 'batter'

class Doughnut(Item):

    name = 'doughnut'

class BetterDoughnut(Item):

    name = 'better_doughnut'

class DoughnutCooked(Item):

    name = 'doughnut_cooked'
