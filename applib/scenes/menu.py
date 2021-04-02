'''applib.scenes.default -- default scene

'''

import math
import random

import applib
import pyglet

from applib import app
from applib.constants import TICK_LENGTH
from applib.engine import animation
from applib.engine import music
from applib.engine import sound

from pyglet.gl import *

POEM_TEXT = '''
Craig and Tom are the bane of the wood
They get up to all the mischief they could
They scrump from Sam's orchard and litter the cores
They filch from poor Mrs Nutkin's stores

But now the fuzz has had enough;
Craig and Tom are finding it rough
to get away with all their hi-jinks.
"We need a decoy, Craig", Tom thinks.

Craig says, "Hey! I've just the plan!"
So Craig and Tom set up a stand
In front of the place they're doing a job
So rather than chase them, The Blue fill their gobs!
'''


class SpiralAnimation(animation.Animation):

    def __init__(self, thing, xname, yname, xtarget, ytarget, angle, duration):
        self.thing = thing
        self.xname = xname
        self.yname = yname
        self.xtarget = xtarget
        self.ytarget = ytarget
        self.angle = angle
        self.duration = duration
        self.elapsed = None
        self.parameter = None
        self.tilt = None

    def start_state(self):
        self.elapsed = 0.0
        origx = getattr(self.thing, self.xname) - self.xtarget
        origy = getattr(self.thing, self.yname) - self.ytarget
        self.parameter = math.hypot(origx, origy) / self.angle
        self.tilt = math.atan2(origy, origx) - self.angle

    def stop_state(self):
        setattr(self.thing, self.xname, self.xtarget)
        setattr(self.thing, self.yname, self.ytarget)
        self.elapsed = None
        self.parameter = None
        self.tilt = None

    def tick(self):
        self.elapsed += TICK_LENGTH
        lerp = max(0, min(1, self.elapsed / self.duration))
        lerp = 3 * lerp ** 2 - 2 * lerp ** 3
        theta = self.angle * (1 - lerp)
        if theta <= 0.0:
            self.stop()
        else:
            radius = self.parameter * theta
            sin, cos = math.sin(theta), math.cos(theta)
            sint, cost = math.sin(self.tilt), math.cos(self.tilt)
            setattr(self.thing, self.xname, self.xtarget + -radius * cos * sint + radius * sin * cost)
            setattr(self.thing, self.yname, self.ytarget + radius * cos * cost + radius * sin * sint)



class MenuScene(object):

    def __init__(self):

        self.overlay = pyglet.resource.texture('overlays/burlap_256.png')

        self.logo_image = pyglet.resource.image('logos/paper_dragon_large.png')
        self.logo_image.anchor_x = self.logo_image.width // 2
        self.logo_image.anchor_y = self.logo_image.height // 2
        self.logo_sprite = pyglet.sprite.Sprite(self.logo_image)
        self.logo_sprite.x = app.window.width // 2
        self.logo_sprite.y = app.window.height // 2
        self.logo_sprite.scale = (app.window.width // 2) / self.logo_image.width
        self.logo_sprite.opacity = 0.0

        self.logo_animation = animation.QueuedAnimation(
            animation.WaitAnimation(1.0, self.do_rawr),
            animation.AttributeAnimation(self.logo_sprite, 'opacity', 255.0, 2.0, 'symmetric'),
            animation.WaitAnimation(2.0),
            animation.AttributeAnimation(self.logo_sprite, 'opacity', 0.0, 2.0),
            animation.WaitAnimation(1.0, self.end_logo),
        ).start()

        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background_color = (255, 255, 255, 255),
            visible = False,
        )

        self.title_image = self.interface.add(
            width = 1.0,
            height = 0.84,
            align_y = 0.58,
            anchor_y = 0.5,
            image_texture = pyglet.resource.texture('interface/title.png')
        )

        self.play_button = self.interface.add(
            align_x = 0.17,
            align_y = 0.08,
            anchor_x = 0.5,
            anchor_y = 0.5,
            height = 0.1,
            text = 'Play',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            font_size = 0.06,
        )

        self.continue_button = self.interface.add(
            align_x = 0.5,
            align_y = 0.08,
            anchor_x = 0.5,
            anchor_y = 0.5,
            height = 0.1,
            text = 'Unused',
            text_bold = True,
            text_color = (0, 0, 0, 255),
            font_size = 0.06,
            visible = False
        )

        self.quit_button = self.interface.add(
            align_x = 0.83,
            align_y = 0.08,
            anchor_x = 0.5,
            anchor_y = 0.5,
            height = 0.1,
            text = 'Quit',
            text_bold = True,
            text_color = (0, 0, 0, 255),
            font_size = 0.06,
        )

        self.interface_x = self.interface.get_content_size()[0] * 1.5
        self.interface_y = -self.interface.get_content_size()[1]

        self.poem = self.interface.add(
            align_x = -1.0,
            align_y = -0.5,
            anchor_x = 0.0,
            anchor_y = 0.0,
        )

        self.poem_text = self.poem.add(
            text = POEM_TEXT,
            text_color = (0, 0, 0, 0),
            font_size = 0.03,
        )

    fade_poem = None
    fade_width = None

    def on_tick(self):
        if self.fade_poem is not None:
            self.poem_text.get_content_size()
            lines = self.poem_text._text_layout.lines
            yvals = []
            trips = []
            for line in lines:
                for vlist in line.vertex_lists:
                    verts = vlist.vertices
                    for i in range(0, len(verts)//2):
                        yv = verts[2*i+1]
                        yvals.append(yv)
                        trips.append((vlist, i, yv))
            maxy = max(yvals)
            miny = min(yvals)
            fade_width = self.fade_width * (maxy - miny)
            fade_max = miny + (1.0 - self.fade_poem) * (maxy - miny + fade_width)
            fade_min = fade_max - fade_width
            for vlist, i, yval in trips:
                col = 0
                if yval > fade_max:
                    col = 255
                elif yval > fade_min:
                    col = min(255, int(256 * (yval - fade_min) / fade_width))
                vlist.colors[4*i+3] = col
            
    rawr_player = None

    def do_rawr(self):
        if self.rawr_player:
            self.rawr_player.pause()
        self.rawr_player = sound.rawr()

    def do_show_poem(self):
        self.fade_poem = 0.0
        self.fade_width = 0.2
        SpiralAnimation(self, 'interface_x', 'interface_y', self.interface.get_content_size()[0], 0.5 * self.interface.get_content_size()[1], 0.25 * math.pi, 1.0).start()
        animation.QueuedAnimation(
            animation.WaitAnimation(1.0),
            animation.AttributeAnimation(self, 'fade_poem', 1.0, 15.0),
            animation.WaitAnimation(3.0, self.do_start),
        ).start()

    def do_start(self):
        app.controller.switch_scene(applib.scenes.level.LevelScene)

    def end_logo(self):
        if self.rawr_player:
            self.rawr_player.pause()
        self.logo_animation.stop()
        self.logo_sprite.visible = False
        self.interface.visible = True
        width, height = self.interface.get_content_size()
        animations = []
        animation.QueuedAnimation(
            SpiralAnimation(self, 'interface_x', 'interface_y', 0.0, 0.0, 0.85 * math.pi, 2.0),
        ).start()

    _hover_button = None

    _press_button = None

    def _update_mouse_position(self, x, y):
        x -= self.interface_x
        y -= self.interface_y
        new_hover_button = \
            'play' if self.play_button.contains(x, y) else \
            'quit' if self.quit_button.contains(x, y) else \
            None

        if (new_hover_button is not None) and (new_hover_button != self._hover_button):
            sound.click()
        self._hover_button = new_hover_button

        self.play_button.text_color = (80, 80, 80, 255) if self._hover_button == 'play' else (0, 0, 0, 255)
        self.quit_button.text_color = (80, 80, 80, 255) if self._hover_button == 'quit' else (0, 0, 0, 255)

    def on_mouse_enter(self, x, y):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_leave(self, x, y):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.interface.visible:
            self._update_mouse_position(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.interface.visible:
            self._update_mouse_position(x, y)
            self._press_button = self._hover_button

    def on_mouse_release(self, x, y, button, modifiers):
        if self.interface.visible:
            self._update_mouse_position(x, y)
            if (self._press_button is not None) and (self._hover_button == self._press_button):
                getattr(self, f'do_button_{self._press_button}')()
            self._press_button = None
        else:
            self.end_logo()

    def do_button_play(self):
        self.do_show_poem()

    def do_button_quit(self):
        pyglet.app.exit()

    def on_draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        app.window.clear()
        self.interface.draw(draw_x=self.interface_x, draw_y=self.interface_y)
        self.logo_sprite.draw()

        # Render overlay
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
        glEnable(self.overlay.target)
        glBindTexture(self.overlay.target, self.overlay.id)
        glTexParameteri(self.overlay.target, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(self.overlay.target, GL_TEXTURE_WRAP_T, GL_REPEAT)
        x, y = map(int, self.interface.get_offset())
        tx, ty = x - self.interface_x, y - self.interface_y
        w, h = map(int, self.interface.get_content_size())
        vertex_data = [x, y, x + w, y, x + w, y + h, x, y + h]
        texture_data = [v / self.overlay.width for v in [tx, ty, tx + w, ty, tx + w, ty + h, tx, ty + h]]
        color_data = [255, 255, 255, 255] * 4
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t2f', texture_data), ('c4B', color_data))
        glPopAttrib()
