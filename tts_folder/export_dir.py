import os

SCRIPT_STATE_FILE = "scriptStates.json"
RELOAD_FILE = ".reload"
STATE_KEY_TO_EXTENSION = {"script": "ttslua", "ui": "xml"}

def get_script_state_path(export_dir):
    return os.path.join(export_dir, SCRIPT_STATE_FILE)


def get_export_filename(item, key):
    extension = STATE_KEY_TO_EXTENSION[key]
    return "{name}-{guid}.{extension}".format(**item, extension=extension)
