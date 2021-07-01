import os

SCRIPT_STATE_FILE = "scriptStates.json"
SCRIPT_HOT_RELOAD_FILE = "scriptHotReloadMap.json"
RELOAD_FILE = ".reload"
STATE_KEY_TO_EXTENSION = {"script": "ttslua", "ui": "xml"}

HOT_RELOAD_TIMES = "times"
HOT_RELOAD_FILES_GUID = "filesGUID"
HOT_RELOAD_GUID_FILES = "GUIDFiles"


def get_script_state_path(export_dir):
    return os.path.join(export_dir, SCRIPT_STATE_FILE)


def get_hot_reload_path(export_dir):
    return os.path.join(export_dir, SCRIPT_HOT_RELOAD_FILE)


def get_export_filename(item, key):
    extension = STATE_KEY_TO_EXTENSION[key]
    return "{name}-{guid}.{extension}".format(**item, extension=extension)


def get_libs_dirs(lib_dirs=None):
    lib_dirs = lib_dirs or []
    lib_dirs = lib_dirs.copy()
    lib_dirs.append(
        os.path.join(os.path.expanduser("~"), "Documents", "Tabletop Simulator")
    )
    return lib_dirs
