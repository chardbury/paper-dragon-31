
import os
os.chdir(os.path.dirname(__file__))

import pyglet
from pyglet.gl import *

window = pyglet.window.Window(width=1080, height=710)
image = pyglet.resource.image('image.jpg')
overlay = pyglet.resource.image('overlay.png')

def draw_texture(texture, alpha=1.0):
    tex = texture.tex_coords
    array = (GLfloat * 60)(
        # Vertex 1
        tex[0], tex[1], tex[2], 1.0,
        alpha, alpha, alpha, alpha,
        0.0, 0.0, 1.0,
        0.0, 0.0, 0.0, 1.0,
        # Vertex 2
        tex[3], tex[4], tex[5], 1.0,
        alpha, alpha, alpha, alpha,
        0.0, 0.0, 1.0,
        texture.width, 0.0, 0.0, 1.0,
        # Vertex 3
        tex[6], tex[7], tex[8], 1.0,
        alpha, alpha, alpha, alpha,
        0.0, 0.0, 1.0,
        texture.width, texture.height, 0.0, 1.0,
        # Vertex 4
        tex[9], tex[10], tex[11], 1.0,
        alpha, alpha, alpha, alpha,
        0.0, 0.0, 1.0,
        0.0, texture.height, 0.0, 1.0,
    )
    glPushAttrib(GL_ENABLE_BIT)
    glEnable(texture.target)
    glBindTexture(texture.target, texture.id)
    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
    glInterleavedArrays(GL_T4F_C4F_N3F_V4F, 0, array)
    glDrawArrays(GL_QUADS, 0, 4)
    glPopClientAttrib()
    glPopAttrib()

@window.event
def on_draw():
    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClear(gl.GL_COLOR_BUFFER_BIT)
    glPushAttrib(GL_ENABLE_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    draw_texture(image)
    draw_texture(overlay, 0.8)
    glPopAttrib()

pyglet.app.run()
