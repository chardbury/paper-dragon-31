'''applib.engine.music -- music playback classes

'''

import applib
import pyglet

from applib import app
from applib.constants import FADE_RATE


class MusicManager(object):
    
    def __init__(self):
        self.player = None
        self.next = None
        self.volume = 1.0
        self.state = 'normal'

    def switch(self, source):
        if self.player:
            self.state = 'fadeout'
            self.next = source
        else:
            self.state = 'fadein'
            self.player = source.play()

    def on_tick(self):
        if self.state == 'fadein':
            self.player.volume = min(self.volume, self.player.volume + FADE_RATE)
            if self.player.volume == self.volume:
                self.state = 'normal'
        elif self.state == 'fadeout':
            self.player.volume = max(0.0, self.player.volume - FADE_RATE)
            if self.player.volume == 0.0:
                if self.next is None:
                    self.state = 'normal'
                    self.player = None
                else:
                    self.state = 'fadein'
                    self.player = self.next.play()
                    self.next = None


music_manager = MusicManager()
