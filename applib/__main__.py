import applib
import pyglet


applib.tools.command.parse_arguments()
applib.tools.settings.load_settings()
applib.tools.resources.prepare_resources()
applib.engine.controller.prepare_controller()
pyglet.app.run()
