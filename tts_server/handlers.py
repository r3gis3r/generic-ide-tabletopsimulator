import glob
import json
import logging
import os

from tts_lua.luabundler import unbundle

log = logging.getLogger("ttshandler")


def _handle_push_new_object(message: dict, *_, **__):
    pass


def _handle_load_new_game(message: dict, *_, export_dir=None, **__):
    if export_dir is None:
        log.info("Ignore game loading since no export dir set")
        return
    script_states = message.get("scriptStates")
    if script_states:
        # Clean folder
        for f in glob.glob(os.path.join(export_dir, "*")):
            os.remove(f)
        # Save raw state
        script_states_save = os.path.join(export_dir, "scriptStates.json")
        with open(script_states_save, "w") as fp:
            json.dump(script_states, fp, indent=4)
        # Save each file
        for item in script_states:
            for extension, key in [("ttslua", "script"), ("xml", "ui")]:
                if not item.get(key):
                    continue

                data = item[key]
                if extension == "ttslua":
                    data = unbundle(data)
                filename = "{name}-{guid}.{extension}".format(
                    **item, extension=extension
                )

                with open(os.path.join(export_dir, filename), "w") as fp:
                    fp.write(data)
    # log.info("Should load game %s in %s", message, project_dir)


def _handle_print(message: dict, *_, **__):
    log.debug("[MSG] %s", message.get("message"))


def _handle_error(message: dict, *_, **__):
    log.error("[ERROR] %s", message.get("error"))


def _handle_default(message: dict, *_, **__):
    log.info("Unknown message %s", message)


def _handle_custom_message(message: dict, *_, **__):
    log.info("Custom message %s", message)


def _handle_save(message: dict, *_, **__):
    log.info("TTS saves %s", message.get("savePath"))


MESSAGES_HANDLERS = {
    0: _handle_push_new_object,
    1: _handle_load_new_game,
    2: _handle_print,
    3: _handle_error,
    6: _handle_save,
}


def process_message(message: dict, **kwargs):
    MESSAGES_HANDLERS.get(message.get("messageID"), _handle_default)(message, **kwargs)
