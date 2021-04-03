import os

PROJECT_DIR_PATH = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR_PATH = os.path.join(PROJECT_DIR_PATH, 'data')
SCENES_DIR_PATH = os.path.join(DATA_DIR_PATH, 'scenes')
VALID_SCENE_DIRECTIVES = {
    'end_game',
    'next_level',
    'play_sound',
    'repeat_level',
    'say_both',
    'say_left',
    'say_right',
    'set_left_image',
    'set_left_name',
    'set_right_image',
    'set_right_name',
    'win_game',
}
IGNORE_SCENE_NAMES = {
    'main_script.txt',
    'todo.txt',
}

for scene_file_name in os.listdir(SCENES_DIR_PATH):
    if scene_file_name not in IGNORE_SCENE_NAMES:
        scene_file_path = os.path.join(SCENES_DIR_PATH, scene_file_name)
        for line in open(scene_file_path, 'r').readlines():
            if len(line.strip()) > 0:
                try:
                    directive, value = map(str.strip, line.split(':', 1))
                    assert directive in VALID_SCENE_DIRECTIVES, scene_file_name
                except:
                    print(scene_file_name)

