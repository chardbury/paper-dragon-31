'''applib.controller -- application controller

'''

import importlib
import logging

import applib
import pyglet

from applib import app
from applib.constants import APPLICATION_NAME
from applib.constants import APPLICATION_VERSION
from applib.constants import TICK_LENGTH
from applib.engine import animation
from applib.engine import music

_logger = logging.getLogger(__name__)


class Controller(pyglet.event.EventDispatcher):
    '''Main controller class to link components together.

    '''

    event_types = (
        'on_tick',
    )

    event_graph = (
        ('window', ('scene', 'keystate')),
        ('controller', ('scene', 'animation', 'music')),
        ('settings', ('scene', 'music')),
    )

    def __init__(self):
        '''Create a `Controller` object.

        '''

        #: The main application window.
        app.window = pyglet.window.Window(
            caption=f'{APPLICATION_NAME} v{APPLICATION_VERSION}',
            fullscreen=app.settings.fullscreen,
        )

        #: The global key state handler.
        app.keystate = pyglet.window.key.KeyStateHandler()
        #: The global music manager.
        app.music = music.MusicManager(volume=app.settings.volume)
        #: The global animation manager.
        app.animation = animation.AnimationManager()

        # Install the main update function.
        self.next_tick = 0.0
        pyglet.clock.schedule_interval(self.update, TICK_LENGTH)

    def switch_scene(self, scene, *args, **kwargs):
        '''Construct and switch to the given scene.

        '''

        # Tear down the current scene.
        if app.scene is not None:
            for dispatcher_name, listener_names in self.event_graph:
                dispatcher = getattr(app, dispatcher_name)
                for listener_name in reversed(listener_names):
                    listener = getattr(app, listener_name)
                    dispatcher.push_handlers(listener)

        # Instantiate or otherwise locate a new scene.
        if isinstance(scene, str):
            scene_module_name, scene_class_name = scene.rsplit('.', 1)
            scene_module = importlib.import_module(scene_module_name)
            scene_class = getattr(scene_module, scene_class_name)
        else:
            scene_class = scene
        app.scene = scene_class(*args, **kwargs)

        # Set up the event handlers around the new scene.
        if app.scene is not None:
            for dispatcher_name, listener_names in self.event_graph:
                dispatcher = getattr(app, dispatcher_name)
                for listener_name in listener_names:
                    listener = getattr(app, listener_name)
                    dispatcher.push_handlers(listener)

    def update(self, delta):
        '''Advance the application state by the given amount of time.

        '''

        # Switch to the start scene if we are not currently in a scene.
        if app.scene is None:
            app.controller.switch_scene(app.settings.start_scene)

        # Process enough ticks to catch up to the present.
        self.next_tick -= delta
        while self.next_tick <= 0.0:
            self.next_tick += TICK_LENGTH
            self.dispatch_event('on_tick')


def prepare_controller():
    '''Create the controller.

    '''
    app.controller = Controller()
