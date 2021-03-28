'''applib.tools.command -- command line arguments

The `parse_arguments` function will parse the command line arguments and store
the resulting namespace as `applib.app.arguments`.

'''

import argparse
import logging
import sys

import applib
import pyglet

from applib import app
from applib.constants import APPLICATION_NAME
from applib.constants import APPLICATION_VERSION
from applib.constants import DEBUG

_logger = logging.getLogger(__name__)


def parse_arguments():
    '''Parse the command line arguments and store the argument namespace.

    '''

    _logger.info('parsing command line arguments')

    parser = argparse.ArgumentParser()

    ## Standard options

    parser.add_argument('-v', '--version',
        action='store_true', dest='version', default=None,
        help='display the version information')
    
    group = parser.add_mutually_exclusive_group()

    group.add_argument('-w', '--windowed',
        action='store_false', dest='fullscreen', default=None,
        help='run in windowed mode')

    group.add_argument('-f', '--fullscreen',
        action='store_true', dest='fullscreen', default=None,
        help='run in fullscreen mode')

    ## Debugging options

    if DEBUG:

        debug_group = parser.add_argument_group('debugging options')

        debug_group.add_argument('--start-scene',
            action='store', dest='start_scene', default=None,
            metavar='SCENE', help='start the application in SCENE')

    # Create and store the arguments namespace.
    app.arguments = parser.parse_args()

    # Exit early if checking version.
    if app.arguments.version:
        print('{} v{}'.format(APPLICATION_NAME, APPLICATION_VERSION))
        sys.exit(0)
