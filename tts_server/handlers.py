import glob
import json
import logging
import os
import re
import tempfile
import time

from tts_folder.export_dir import (
    get_script_state_path,
    get_export_filename,
    RELOAD_FILE,
    get_libs_dirs,
)
from tts_lua.constants import (
    TTS_MSG_PUSH_NEW_OBJECT,
    TTS_MSG_LOAD_NEW_GAME,
    TTS_MSG_PRINT,
    TTS_MSG_ERROR,
    TTS_MSG_SAVE,
    TTS_IDE_MSG_PROGRESS,
)
from tts_lua.luabundler import unbundle_file
from tts_server.progress_bar import print_progress_bar

log = logging.getLogger("ttshandler")


def _handle_push_new_object(message: dict, export_dir=None, *_, **__):
    if export_dir is None:
        log.info("Ignore file load since export dir not set")
        return
    script_states = message.get("scriptStates", []) or []
    script_states_save = get_script_state_path(export_dir=export_dir)
    existing_script_states = None
    existing_script_by_guid = {}
    if os.path.exists(script_states_save):
        try:
            with open(script_states_save, "rb") as fp:
                existing_script_states = json.load(fp)
            existing_script_by_guid = {
                it["guid"]: it for it in existing_script_states
            }
        except:
            log.error("Failed to reload script states", exc_info=True)

    _import_script_states(script_states, export_dir=export_dir, create_empty_files=True)

    for item in script_states:
        script_name = get_export_filename(item, key="script")
        script_path = os.path.join(export_dir, script_name)
        print(f"{script_path}:0:1 : open requested by TabletopSimulator")
        if existing_script_states:
            if item["guid"] in existing_script_by_guid:
                existing_script_by_guid[item["guid"]] = item
            else:
                existing_script_states.append(item)

    if existing_script_states:
        with open(script_states_save, "w") as fp:
            json.dump(existing_script_states, fp, indent=4)


def _handle_load_new_game(message: dict, *_, export_dir=None, **__):
    if export_dir is None:
        log.info("Ignore game loading since no export dir set")
        return
    script_states = message.get("scriptStates")
    if script_states:
        script_states_save = get_script_state_path(export_dir=export_dir)
        # Clean folder - only if one script save found
        if os.path.exists(script_states_save):
            for f in glob.glob(os.path.join(export_dir, "*")):
                os.remove(f)
        # Save raw state
        with open(script_states_save, "w") as fp:
            json.dump(script_states, fp, indent=4)
        # Save each file
        _import_script_states(script_states, export_dir)
        reload_path = os.path.join(export_dir, RELOAD_FILE)
        with open(reload_path, "w") as fp:
            fp.write(str(time.time()))
        log.info("Reload files complete")
    # log.info("Should load game %s in %s", message, project_dir)


def _import_script_states(script_states, export_dir, create_empty_files=False):
    with tempfile.TemporaryDirectory(prefix="tts_") as tmpdir:
        for item in script_states:
            for extension, key in [("ttslua", "script"), ("xml", "ui")]:
                data = item.get(key)
                dont_create = not data
                if create_empty_files:
                    dont_create = data is None
                if dont_create:
                    continue

                if isinstance(data, str):
                    data = data.encode("utf-8")
                data = data or b""

                # Final file name
                filename = get_export_filename(item, key=key)

                # In case of script, unbundle it through temp dir
                if data and key == "script":
                    temp_target_file = os.path.join(tmpdir, filename)
                    with open(temp_target_file, "wb") as fp:
                        fp.write(data)
                    new_data = unbundle_file(temp_target_file)
                    if new_data:
                        data = new_data
                # Export the final file
                target_file = os.path.join(export_dir, filename)
                with open(target_file, "wb") as fp:
                    fp.write(data)


def _handle_print(message: dict, *_, **__):
    log.info("[MSG] %s", message.get("message"))


def _handle_error(message: dict, *_, export_dir=None, lib_dirs=None, **__):
    guid = message.get("guid")
    if not guid:
        log.error("Unknow error %s", message)
        return
    script_states_save = get_script_state_path(export_dir=export_dir)
    with open(script_states_save, "r") as fp:
        states = json.load(fp)
    guid_states = [st for st in states if st.get("guid") == guid]
    if not guid_states:
        log.error("Not found error %s", message)
        return
    item = guid_states[0]
    error_str = message.get("error")
    row = 0
    column = 0
    row_string = re.match(r".*:\(([0-9]+),([^)]+)\):.*", error_str)
    if row_string:
        row = int(row_string.group(1)) - 1
        column = row_string.group(2)
    script_path = os.path.join(export_dir, get_export_filename(item, key="script"))
    lines = item["script"].splitlines()
    interesting_line = lines[row]
    interesting_lines = lines[:row]
    for idx, l in enumerate(reversed(interesting_lines)):
        bundle = re.match(r"\s*__bundle_register\(\"([^\"]+)\",.+\).*", l)
        if bundle:
            lib_dirs = get_libs_dirs(lib_dirs)
            required_package = bundle.group(1)
            required_path = required_package.replace(".", os.path.sep)
            script_path = f"{required_path}.ttslua"
            row = idx + 1
            for lib_dir in lib_dirs:
                candidate_path = os.path.join(lib_dir, script_path)
                if os.path.exists(candidate_path):
                    script_path = candidate_path
                    break
            break
    print(
        f"{script_path}:{row}:{column} [ERROR] {error_str} CODE: {interesting_line.strip()}"
    )


def _handle_default(message: dict, *_, **__):
    log.info("Unknown message %s", message)


def _handle_custom_message(message: dict, *_, **__):
    log.info("Custom message %s", message)


def _handle_save(message: dict, *_, **__):
    log.info("TTS saves %s", message.get("savePath"))


def _handle_progress(message: dict, *_, **__):
    print_progress_bar(**message)


MESSAGES_HANDLERS = {
    TTS_MSG_PUSH_NEW_OBJECT: _handle_push_new_object,
    TTS_MSG_LOAD_NEW_GAME: _handle_load_new_game,
    TTS_MSG_PRINT: _handle_print,
    TTS_MSG_ERROR: _handle_error,
    TTS_MSG_SAVE: _handle_save,
    TTS_IDE_MSG_PROGRESS: _handle_progress,
}


def process_message(message: dict, **kwargs):
    MESSAGES_HANDLERS.get(message.get("messageID"), _handle_default)(message, **kwargs)
