'''applib.engine.music -- music playback classes

'''

import applib
import pyglet

from applib import app
from applib.constants import FADE_RATE
from applib.constants import TICK_LENGTH


class MusicManager(object):
    '''Music manager class supporting a single concurrent music track.

    '''
    
    def __init__(self, volume=0.5):
        '''Construct a MusicManager object.

        '''
        self.volume = volume
        self.player = None
        self.next = None
        self.state = 'normal'

    def switch(self, source):
        '''Switch the music manager to a different source.

        '''
        if self.player:
            self.state = 'fadeout'
        self.next = source

    def on_tick(self):

        # While in 'fadein', adjust volume up each tick...
        if self.state == 'fadein':
            self.player.volume = min(self.volume, self.player.volume + FADE_RATE * TICK_LENGTH)
            # Until we reach the target volume, then move to 'normal'.
            if self.player.volume == self.volume:
                self.state = 'normal'

        # While in 'fadeout', adjust the volume down each tick...
        elif self.state == 'fadeout':
            self.player.volume = max(0.0, self.player.volume - FADE_RATE * TICK_LENGTH)
            # Until we reach the target volume, then move to 'normal' and remove the player.
            if self.player.volume == 0.0:
                self.state = 'normal'
                self.player = None

        # If in 'normal', move to 'fadein' and open the next source
        elif self.state == 'normal':
            if self.next is not None:
                self.state = 'fadein'
                self.player = self.next.play()
                self.next = None
