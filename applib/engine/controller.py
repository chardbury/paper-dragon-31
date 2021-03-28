'''applib.controller -- application controller

'''

import importlib
import logging

import applib
import pyglet

from applib import app
from applib.constants import APPLICATION_NAME
from applib.constants import APPLICATION_VERSION
from applib.constants import DEBUG
from applib.constants import TICK_LENGTH
from applib.engine import animation
from applib.engine import music

_logger = logging.getLogger(__name__)


class Controller(pyglet.event.EventDispatcher):
    '''Main controller class to link components together.

    '''

    event_types = (
        'on_scene_start',
        'on_scene_finish',
        'on_tick',
    )

    def __init__(self):
        '''Create a Controller object.

        '''

        # Create the application window.
        window_caption = f'{APPLICATION_NAME} v{APPLICATION_VERSION}'
        app.window = pyglet.window.Window(
            caption=window_caption,
            fullscreen=False,
        )

        # Create the global key state handler.
        app.keystate = pyglet.window.key.KeyStateHandler()

        # Create the global music manager.
        app.music = music.MusicManager(volume=0.5)

        # Install the main update function.
        self.next_tick = 0.0
        pyglet.clock.schedule_interval(self.update, TICK_LENGTH)
        
        # Prepare the event stacks.
        self.scene_dispatchers = [self, app.window]
        self.controller_listeners = [animation.animation_manager, app.music]
        self.window_listeners = [app.keystate]

        # Switch to the initial scene.
        self.current_scene = None
        self.switch_scene('applib.scenes.default.DefaultScene')

    def switch_scene(self, scene, *args, **kwargs):
        '''Construct and switch to the given scene.

        '''

        # Tear down the current scene.
        if self.current_scene is not None:
            self.dispatch_event('on_scene_finish')
            for listener in self.window_listeners:
                app.window.remove_handlers(listener)
            for listener in self.controller_listeners:
                self.remove_handlers(listener)
            for dispatcher in self.scene_dispatchers:
                dispatcher.remove_handlers(self.current_scene)

        # Instantiate or otherwise locate a new scene.
        if isinstance(scene, str):
            scene_module_name, scene_class_name = scene.rsplit('.', 1)
            scene_module = importlib.import_module(scene_module_name)
            scene_class = getattr(scene_module, scene_class_name)
        else:
            scene_class = scene
        self.current_scene = scene_class(*args, **kwargs)

        # Set up the event handlers around the new scene.
        if self.current_scene is not None:
            for dispatcher in self.scene_dispatchers:
                dispatcher.push_handlers(self.current_scene)
            for listener in reversed(self.controller_listeners):
                self.push_handlers(listener)
            for listener in reversed(self.window_listeners):
                app.window.push_handlers(listener)
            self.dispatch_event('on_scene_start')

    def update(self, delta):
        '''Advance the application state by the given amount of time.

        '''
        self.next_tick -= delta
        while self.next_tick <= 0.0:
            self.next_tick += TICK_LENGTH
            self.dispatch_event('on_tick')


def prepare_controller():
    '''Create the controller.

    '''
    app.controller = Controller()
