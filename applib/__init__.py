'''applib -- main application library

'''


class app(object):
    animation = None
    arguments = None
    controller = None
    keystate = None
    music = None
    scene = None
    settings = None
    window = None


def set_pyglet_options():
    '''Set options before we import pyglet submodules.

    '''

    import pyglet
    pyglet.options.update({
        'shadow_window': False,
    })

set_pyglet_options()
del set_pyglet_options


def prepare_resources():
    '''Set the appropriate resource paths.

    '''

    import os

    import applib 
    import pyglet

    # Set resource paths.
    applib_directory = os.path.abspath(os.path.dirname(applib.__file__))
    data_directory = os.path.abspath(os.path.join(applib_directory, '..', 'data'))
    pyglet.resource.path = [data_directory]
    pyglet.resource.reindex()

    # Install fonts.
    fonts_directory = os.path.join(data_directory, 'fonts')
    for root, directory_names, file_names in os.walk(fonts_directory):
        for file_name in file_names:
            if file_name.rsplit('.', 1)[1] in ('otf', 'ttf'):
                file_path = os.path.join(root, file_name)
                pyglet.font.add_file(file_path)

prepare_resources()


from . import constants
from . import engine
from . import main
from . import model
from . import scenes
from . import tools
