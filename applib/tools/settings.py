'''applib.tools.settings -- application settings

The `load_settings` function will read the settings file and store the
resulting `Settings` namespace as `applib.app.settings`. If any command line
arguments match a setting name the value of that setting will be overridden
for this invocation.

'''

import copy
import json
import os

import applib
import pyglet

from applib import app
from applib.constants import APPLICATION_NAME
from applib.constants import SETTINGS_FILE
from applib.constants import SETTINGS_DEFAULTS


class Settings(pyglet.event.EventDispatcher):

    event_types = ('on_setting_change',)

    def __init__(self):
        '''Construct a `Settings` object.

        '''
        self.reset_settings()

    def __getattr__(self, name):
        '''Retrieve a value from the namespace dictionary.

        '''
        if name in SETTINGS_DEFAULTS:
            return self._data[name]
        else:
            raise AttributeError('no such setting: %r' % name)

    def __setattr__(self, name, value):
        '''Update a value in the namespace dictionary.

        '''
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in SETTINGS_DEFAULTS:
            if not isinstance(value, type(SETTINGS_DEFAULTS[name])):
                raise TypeError('incorrect type for %s: %r' % (name, value))
            if self._data[name] != value:
                self.dispatch_event('on_setting_change', name, value)
                self._data[name] = value
        else:
            raise AttributeError('no such setting: %r' % name)

    def reset_settings(self):
        '''Reset the settings to their default state.

        '''
        self._data = copy.deepcopy(SETTINGS_DEFAULTS)
        self._saved = {}

    def get_settings_file(self):
        '''Ensure that the settings file exists and return its path.

        '''
        settings_path = pyglet.resource.get_settings_path(APPLICATION_NAME)
        settings_file = os.path.join(settings_path, SETTINGS_FILE)
        if not os.path.exists(settings_path):
            os.makedirs(settings_path)
        if not os.path.exists(settings_file):
            json.dump({}, open(settings_file, 'w'))
        return settings_file

    def load_settings(self):
        '''Load the settings file and update the settings object.

        '''
        self._saved.clear()
        settings_file = self.get_settings_file()
        loaded_settings = json.load(open(settings_file))
        for key, value in loaded_settings.items():
            setattr(self, key, value)
            self._saved[key] = value

    def save_settings(self, **kwargs):
        '''Update any number of settings and save them to the settings file.

        '''
        for key, value in kwargs.items():
            setattr(self, key, value)
            self._saved[key] = value
        settings_file = self.get_settings_file()
        json.dump(self._saved, open(settings_file, 'w'), indent=4)


def load_settings():
    '''Create and populate the settings namespace.

    '''

    # Create the default settings.
    app.settings = Settings()
    app.settings.load_settings()

    # Populate compatible settings from the command line.
    for name in SETTINGS_DEFAULTS:
        argument_value = getattr(app.arguments, name, None)
        if type(argument_value) is type(SETTINGS_DEFAULTS[name]):
            setattr(app.settings, name, argument_value)
