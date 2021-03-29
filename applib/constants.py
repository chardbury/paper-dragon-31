'''applib.constants -- application constants

'''


## Debug

DEBUG = bool(__import__('os').environ.get('APPLIB_DEBUG', '').strip())


## Application

APPLICATION_NAME = 'Untitled Application'

APPLICATION_VERSION = '0.1'


## Clock

TICK_RATE = 60.0

TICK_LENGTH = 1.0 / TICK_RATE


## Music

MUSIC_FADE_RATE = 0.35

MUSIC_FADE_GRACE = 0.5


## Settings

SETTINGS_FILE = 'settings.json'

SETTINGS_DEFAULTS = {
    'fullscreen': False,
    'start_scene': 'applib.scenes.level.LevelScene',
    'volume': 0.5,
}


## GRAPHICS

ITEM_SCALE = 0.1

DEVICE_SCALE = 0.2
