import time

import applib
import pyglet


def main():
    applib.tools.command.parse_arguments()
    applib.tools.settings.load_settings()
    applib.engine.controller.prepare_controller()
    pyglet.app.run()
    time.sleep(0.1)
