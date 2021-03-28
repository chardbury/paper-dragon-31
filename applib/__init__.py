'''applib -- main application library

'''

@type.__call__
class app(object):
    animation = None
    controller = None
    keystate = None
    music = None
    scene = None
    window = None

from . import constants
from . import engine
from . import scenes
from . import tools
