'''applib -- main application library

'''

@type.__call__
class app(object):
    __slots__ = [
        'controller',
        'keystate',
        'window',
    ]

from . import constants
from . import engine
from . import scenes
from . import tools


def init():
    engine.resources.prepare_resources()
    engine.controller.prepare_controller()
