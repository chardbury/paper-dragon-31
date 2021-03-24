import pyglet

window = pyglet.window.Window()

label = pyglet.text.Label(
    text = 'It Works!',
    font_size = 0.06 * window.height,
    x = window.width // 2,
    y = window.height // 2,
    anchor_x = 'center',
    anchor_y = 'center',
)

@window.event
def on_draw():
    label.draw()

pyglet.app.run()