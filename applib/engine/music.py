'''applib.engine.music -- music playback classes

'''

import applib
import pyglet

from applib import app
from applib.constants import MUSIC_FADE_GRACE
from applib.constants import MUSIC_FADE_RATE
from applib.constants import TICK_LENGTH


class MusicManager(object):
    '''Music manager class supporting a single concurrent music track.

    '''
    
    def __init__(self):
        '''Construct a MusicManager object.

        '''
        self.volume = app.settings.music_volume * app.settings.volume
        self.state = 'normal'
        self.player = None
        self.next = None
        self.grace = None
        self.frate = None

    def switch(self, source, frate=None):
        '''Switch the music manager to a different source.

        '''
        if self.player:
            self.state = 'fadeout'
            self.frate = frate
        self.next = source

    def on_tick(self):
        '''Update the player based on the manager's state.

        '''
        # While in 'fadeout', adjust the volume down each tick...
        if self.state == 'fadeout':
            self.player.volume = max(0.0, self.player.volume - (self.frate or MUSIC_FADE_RATE) * TICK_LENGTH)
            # Until we reach the target volume, then move to 'fadegrace'.
            if self.player.volume == 0.0:
                self.state = 'fadegrace'
                self.grace = MUSIC_FADE_GRACE

        # While in 'fadegrace', adjust the grace down each tick...
        elif self.state == 'fadegrace':
            self.grace = max(0.0, self.grace - TICK_LENGTH)
            # Until we reach zero, then move to 'normal' and remove the player.
            if self.grace == 0.0:
                self.state = 'normal'
                self.player = None

        # If in 'normal', try to open the next source
        elif self.state == 'normal':
            if self.next is not None:
                self.player = self.next.play()
                self.player.volume = self.volume
                self.next = None

    def on_setting_change(self, name, value):
        if name == 'volume':
            self.volume = app.settings.music_volume * value
            if self.state == 'normal':
                self.player.volume = self.volume
        if name == 'music_volume':
            self.volume = value * app.settings.volume
            if self.state == 'normal':
                self.player.volume = self.volume
