'''applib.controller -- application controller

'''

import importlib

import applib
import pyglet

from applib import app
from applib.constants import APPLICATION_NAME
from applib.constants import APPLICATION_VERSION
from applib.constants import DEFAULT_SCREEN_SIZE
from applib.constants import TICK_LENGTH
from applib.engine import animation
from applib.engine import music


class Controller(pyglet.event.EventDispatcher):
    '''Main controller class to link components together.

    '''

    event_types = (
        'on_tick',
        'on_scene_end',
    )

    event_graph = (
        ('window', ('scene', 'keystate')),
        ('controller', ('animation', 'scene', 'music')),
        ('settings', ('scene', 'music')),
    )

    def __init__(self):
        '''Create a `Controller` object.

        '''

        #: The main application window.
        app.window = pyglet.window.Window(
            caption=f'{APPLICATION_NAME} v{APPLICATION_VERSION}',
            fullscreen=app.settings.fullscreen,
            width=(DEFAULT_SCREEN_SIZE[0] if not app.settings.fullscreen else None),
            height=(DEFAULT_SCREEN_SIZE[1] if not app.settings.fullscreen else None),
            visible=False,
        )
        app.window.set_icon(pyglet.resource.image('icons/icon.ico'))


        #: The global key state handler.
        app.keystate = pyglet.window.key.KeyStateHandler()
        #: The global music manager.
        app.music = music.MusicManager()
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
            self.dispatch_event('on_scene_end')
            for dispatcher_name, listener_names in self.event_graph:
                dispatcher = getattr(app, dispatcher_name)
                for listener_name in reversed(listener_names):
                    listener = getattr(app, listener_name)
                    dispatcher.remove_handlers(listener)

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
            if app.settings.level:
                app.settings.start_scene = 'applib.scenes.level.LevelScene'
            app.controller.switch_scene(app.settings.start_scene)

        # Process enough ticks to catch up to the present.
        self.next_tick -= delta
        while self.next_tick <= 0.0:
            self.next_tick += TICK_LENGTH
            self.dispatch_event('on_tick')

        if not app.window.visible:
            app.window.set_visible(True)


def prepare_controller():
    '''Create the controller.

    '''
    app.controller = Controller()
