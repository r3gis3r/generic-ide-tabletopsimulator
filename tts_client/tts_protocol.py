import asyncio
import json
import logging
import os
import time
from functools import partial

from tts_folder.export_dir import (
    get_script_state_path,
    get_export_filename,
    RELOAD_FILE,
)
from tts_lua.luabundler import bundle

log = logging.getLogger("ttsclient")


def request_command_push(*_, export_dir=None, **__):
    state_file = get_script_state_path(export_dir=export_dir)
    script_states = []
    with open(state_file, "r") as fp:
        old_script_states = json.load(fp)
    for item in old_script_states:
        new_item = item.copy()
        for key in ("script", "ui"):
            new_filename = get_export_filename(item, key=key)
            new_filepath = os.path.join(export_dir, new_filename)
            if not os.path.exists(new_filepath):
                log.warning(
                    "File %s doesn't exists while present in last retrieved state",
                    new_filename,
                )
                continue

            if key == "script":
                data = bundle(
                    new_filepath,
                    include_folders=[
                        os.path.join(
                            os.path.expanduser("~"), "Documents", "Tabletop Simulator"
                        )
                    ],
                )
                data = data.decode()
            else:
                with open(new_filepath) as fp:
                    data = fp.read()
            print(key)
            print(data)
            new_item[key] = data
        script_states.append(new_item)
    log.info("Requesting push")
    return {"messageID": 1, "scriptStates": script_states}


def request_command_pull(*_, **__):
    return {"messageID": 0}


def request_command_error(command=None, *_, **__):
    raise ValueError(f"Command {command} not recognized")


REQUESTS_COMMANDS = {"push": request_command_push, "pull": request_command_pull}


async def wait_for_file(file_path, sleep_step=0.2, max_sleep=40):
    tref = time.time()
    while not os.path.exists(file_path):
        await asyncio.sleep(sleep_step)
        if time.time() > tref + max_sleep:
            break
    if os.path.exists(file_path):
        with open(file_path, "r") as fp:
            log.info("Reload done at %s", fp.read())
    else:
        log.info("Wait timeout after %s sec", max_sleep)

async def tts_query(command, host="localhost", port=39999, **kwargs):
    reader, writer = await asyncio.open_connection(host=host, port=port)
    request_func = REQUESTS_COMMANDS.get(
        command, partial(request_command_error, command=command)
    )
    export_dir = kwargs.get("export_dir")
    wait_file_path = None
    if command == "pull" and export_dir:
        wait_file_path = os.path.join(export_dir, RELOAD_FILE)
        os.remove(wait_file_path)

    message = request_func(**kwargs)
    writer.write(json.dumps(message).encode())
    await writer.drain()

    log.debug("Close the connection")
    writer.close()
    await writer.wait_closed()

    if wait_file_path:
        await wait_for_file(wait_file_path)
