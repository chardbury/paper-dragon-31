'''applib.constants -- application constants

'''


## Environment Flags

DEBUG = bool(__import__('os').environ.get('APPLIB_DEBUG', '').strip())


## Application

APPLICATION_NAME = 'Untitled Application'

APPLICATION_VERSION = '0.1'

TICK_RATE = 60.0

TICK_LENGTH = 1.0 / TICK_RATE
