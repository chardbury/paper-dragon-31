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
Patches and Flynn were the bane of the wood;
They got up to all of the mischief they could.
They scrumped from Sam's orchard and littered the cores.
They filched them from poor Mrs Appleby's stores.

But now that the fuzz is on to their stuff;
Patches and Flynn are finding it rough
To steal the apples and all their hijinks.
"We need a decoy", says Patches. Flynn thinks.

Then Flynn says, "Hey! I've got just the plan!"
So Patches and Flynn did set up a stand
In front of the places they're pulling their jobs
So rather than chase them, The Blue stuff their gobs!
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

        self.apple_tex = pyglet.resource.texture('items/apple.png')

        self.interface = applib.engine.panel.Panel(
            aspect = (16, 9),
            background_color = (225, 208, 183, 255),
            visible = False,
            draw_function = self.draw_apple_overlay,
        )

        self.title_image = self.interface.add(
            width = 0.4,
            height = 0.9,
            align_x = 0.25,
            align_y = 0.5,
            anchor_x = 0.5,
            anchor_y = 0.5,
            image_texture = pyglet.resource.texture('interface/title.png'),
        )

        self.title_box = self.interface.add(
            width = 0.45,
            height = 0.25,
            align_x = 0.70,
            align_y = 0.7,
            anchor_x = 0.5,
            anchor_y = 0.0,
            text = 'Copcake Caper',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            font_size = 0.07,
        )

        self.play_button = self.interface.add(
            align_x = 0.70,
            align_y = 0.6,
            anchor_x = 0.5,
            anchor_y = 1.0,
            height = 0.1,
            text = 'Story',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            font_size = 0.06,
        )

        self.endless_button = self.interface.add(
            align_x = 0.70,
            align_y = 0.45,
            anchor_x = 0.5,
            anchor_y = 1.0,
            height = 0.1,
            text = 'Endless',
            text_color = (0, 0, 0, 255),
            text_bold = True,
            font_size = 0.06,
        )

        self.quit_button = self.interface.add(
            align_x = 0.70,
            align_y = 0.3,
            anchor_x = 0.5,
            anchor_y = 1.0,
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
            text_color = (0, 0, 0, 255),
            font_size = 0.03,
            draw_function = self.draw_poem_overlay,
        )

        self.scene_fade = 1.0
        animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 0.0, 1.0),
        ).start()

    fade_poem = None
    fade_width = None

    def on_tick(self):
        if self.scene_fade > 0.0:
            return
        # if self.fade_poem is not None:
        #     self.poem_text.get_content_size()
        #     lines = self.poem_text._text_layout.lines
        #     yvals = []
        #     line_yvals = []
        #     trips = []
        #     for li, line in enumerate(lines):
        #         line_yvals.append([])
        #         for vlist in line.vertex_lists:
        #             verts = vlist.vertices
        #             for i in range(0, len(verts)//2):
        #                 yv = verts[2*i+1]
        #                 yvals.append(yv)
        #                 line_yvals[-1].append(yv)
        #                 trips.append((vlist, i, li, yv))
        #     line_maxy = list(map(max, line_yvals))
        #     line_miny = list(map(min, line_yvals))
        #     maxy = max(yvals)
        #     miny = min(yvals)
        #     fade_width = self.fade_width * (maxy - miny)
        #     fade_max = miny + (1.0 - self.fade_poem) * (maxy - miny + fade_width)
        #     fade_min = fade_max - fade_width
        #     fade_y = (1 - self.fade_poem) * (maxy - miny)
        #     for vlist, i, li, yval in trips:
        #         col = 0
        #         lmin = line_miny[li]
        #         lmax = line_maxy[li]
        #         if lmin > fade_y:
        #             col = 255
        #         elif lmax < fade_y:
        #             col = 0
        #         elif lmax > lmin:
        #             colf = (fade_y - line_miny[li]) / (line_maxy[li] - line_miny[li])
        #             col = max(0, min(255, int(256 * colf)))
        #         else:
        #             col = 0
        #         vlist.colors[4*i+3] = col
            
    rawr_player = None

    def do_rawr(self):
        if self.rawr_player:
            self.rawr_player.pause()
        self.rawr_player = sound.rawr()

    poem_animation = None
    def do_show_poem(self):
        self.fade_poem = 0.05
        self.fade_width = 0.1
        self.poem_animation = animation.QueuedAnimation(
                animation.ParallelAnimation(
                    SpiralAnimation(self, 'interface_x', 'interface_y', self.interface.get_content_size()[0], 0.5 * self.interface.get_content_size()[1], 0.25 * math.pi, 1.0),
                    animation.AttributeAnimation(self, 'fade_poem', 1.0, 20.0),
                ),
                animation.WaitAnimation(10.0, self.do_start),
        ).start()

    def do_start(self):
        self.scene_fade = 0.0
        animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 1.0, 1.0),
            animation.WaitAnimation(0.2, app.controller.switch_scene, applib.scenes.level.LevelScene),
        ).start()

    def end_logo(self):
        if self.rawr_player:
            self.rawr_player.pause()
        self.logo_animation.stop()
        self.logo_sprite.visible = False
        self.interface.visible = True
        width, height = self.interface.get_content_size()
        animations = []
        animation.ParallelAnimation(
            animation.WaitAnimation(0.0, app.music.switch, pyglet.resource.media('music/scott_gratton_rocket_boat.mp3')),
            SpiralAnimation(self, 'interface_x', 'interface_y', 0.0, 0.0, 0.85 * math.pi, 2.0),
        ).start()

    def end_poem(self, now=True):
        if self.poem_animation:
            self.poem_animation.stop()

    _buttons = ['play', 'quit', 'endless']

    _hover_button = None
    _hover_panel = None

    _press_button = None

    def _update_mouse_position(self, x, y):
        x -= self.interface_x
        y -= self.interface_y
        for button in self._buttons:
            if getattr(self, f'{button}_button').contains(x, y):
                new_hover_button = button
                break
        else:
            new_hover_button = None

        if (new_hover_button is not None) and (new_hover_button != self._hover_button):
            sound.click()

        self._hover_button = new_hover_button
        self._hover_panel = getattr(self, f'{new_hover_button}_button') if new_hover_button else None

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
            if self.fade_poem is not None:
                for anim in app.animation:
                    if getattr(anim, 'name', '') == 'fade_poem':
                        anim.elapsed += 20.0
                        break
                else:
                    self.end_poem()
            else:
                if (self._press_button is not None) and (self._hover_button == self._press_button):
                    getattr(self, f'do_button_{self._press_button}')()
                self._press_button = None
        else:
            self.end_logo()

    def do_button_play(self):
        self.do_show_poem()

    def do_button_quit(self):
        animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 1.0, 0.3),
            animation.WaitAnimation(0.1, pyglet.app.exit),
        ).start()

    def do_button_endless(self):
        self.scene_fade = 0.0
        animation.QueuedAnimation(
            animation.AttributeAnimation(self, 'scene_fade', 1.0, 1.0),
            animation.WaitAnimation(0.2, app.controller.switch_scene, applib.scenes.level.LevelScene, applib.model.level.EndlessLevel),
        ).start()

    def draw_poem_overlay(self, x, y):
        if self.fade_poem is not None:
            w, h = self.poem_text.get_content_size()
            fwid = self.fade_width * h
            flen = h + fwid
            ftop = y + h - (self.fade_poem * flen - fwid)
            fbot = ftop - fwid
            pyglet.graphics.draw(12, GL_QUADS,
                ('v2f', [
                    x, y, x + w, y, x + w, fbot, x, fbot,
                    x, fbot, x + w, fbot, x + w, ftop, x, ftop,
                    x, ftop, x + w, ftop, x + w, y + h, x, y + h,
                ]),
                ('c4B',
                    [225, 208, 183, 255] * 6 +
                    [225, 208, 183, 0] * 6
                ),
            )

    def draw_apple_overlay(self, draw_x, draw_y):
        if self._hover_panel:
            px, py = self._hover_panel.get_offset()
            pw, ph = self._hover_panel.get_content_size()
            s = ph
            px += draw_x - s - s/2
            py += draw_y
            glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
            glEnable(self.apple_tex.target)
            glBindTexture(self.apple_tex.target, self.apple_tex.id)
            pyglet.graphics.draw(4, GL_QUADS,
                ('v2f', [px, py, px+s, py, px+s, py+s, px, py+s]),
                ('t3f', self.apple_tex.tex_coords),
                ('c4B', [255] * 16),
                )
            glPopAttrib()

    def on_draw(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)
        
        x, y = map(int, self.interface.get_offset())
        w, h = map(int, self.interface.get_content_size())
        glEnable(GL_SCISSOR_TEST)
        r = app.window.get_pixel_ratio()
        glScissor(int(x*r), int(y*r), int(w*r), int(h*r))

        color = [225, 208, 183, 255]
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', [x, y, x+w, y, x+w, y+h, x, y+h]), ('c4B', color * 4))

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
        x, y = 0, 0
        w, h = app.window.get_size()
        vertex_data = [x, y, x + w, y, x + w, y + h, x, y + h]
        texture_data = [v / self.overlay.width for v in [tx, ty, tx + w, ty, tx + w, ty + h, tx, ty + h]]
        color_data = [255, 255, 255, 200] * 4
        pyglet.graphics.draw(4, GL_QUADS, ('v2f', vertex_data), ('t2f', texture_data), ('c4B', color_data))
        glPopAttrib()

        # Render fade
        if self.scene_fade is not None:
            w, h = app.window.get_size()
            alpha = max(0, min(255, int(256*self.scene_fade)))
            color = [0, 0, 0, alpha]
            pyglet.graphics.draw(4, GL_QUADS, ('v2f', [0,0,w,0,w,h,0,h]), ('c4B', color*4))

        glDisable(GL_SCISSOR_TEST)
