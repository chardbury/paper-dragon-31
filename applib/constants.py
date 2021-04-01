'''applib.constants -- application constants

'''


## Debug

DEBUG = bool(__import__('os').environ.get('APPLIB_DEBUG', '').strip())


## Application

APPLICATION_NAME = 'Untitled Application'

APPLICATION_VERSION = '0.1'

DEFAULT_SCREEN_SIZE = (800, 450)


## Clock

TICK_RATE = 60.0

TICK_LENGTH = 1.0 / TICK_RATE


## Music

MUSIC_FADE_RATE = 0.35

MUSIC_FADE_GRACE = 0.5


## Settings

SETTINGS_FILE = 'settings.json'

SETTINGS_DEFAULTS = {
    'fullscreen': not DEBUG,
    'start_scene': 'applib.scenes.menu.MenuScene',
    'level': 0,
    'volume': 0.5,
}


## Graphics

CURSOR_SCALE = 0.1

DEVICE_SCALE = 0.2

ITEM_SCALE = 0.1

SCENERY_SCALE = 1.0


## Animation

ANIMATION_ZOOM_RATE = 0.15


## Customers

CUSTOMER_SCALE = 0.4

CUSTOMER_POSITIONS = [
    [],
    [0.0],
    [-0.3, 0.3],
    [-0.5, 0.0, 0.5],
    [-0.6, -0.2, 0.2, 0.6],
]

CUSTOMER_BOUNCE_DISTANCE = 0.01

CUSTOMER_BOUNCE_SPEED = 2.0

CUSTOMER_WALK_SPEED = 0.2

CUSTOMER_ORDER_HEIGHT = 0.01

CUSTOMER_ORDER_POSITIONS = [
    [],
    [0.0],
    [-15.0, 15.0],
    [-30.0, 0.0, 30.0],
]

CUSTOMER_PATIENCE_BAR_VERTICAL_OFFSET = 0.0

CUSTOMER_PATIENCE_BAR_MARGIN = 0.02

CUSTOMER_PATIENCE_BAR_HEIGHT = 0.02


## Scenery

COUNTER_EDGE_ADJUSTMENT = -8 / 1152

## Score

MAX_SCORE_FROM_CUSTOMER = 40

PROGRESS_BAR_MARGIN = 0.02
PROGRESS_BAR_WIDTH = 0.3
PROGRESS_BAR_HEIGHT = 0.03
