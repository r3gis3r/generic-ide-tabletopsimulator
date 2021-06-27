import asyncio
import json
import logging
import os
import time
from functools import partial

from tts_client.direct_ide import IDECommunication
from tts_folder.export_dir import (
    get_script_state_path,
    get_export_filename,
    RELOAD_FILE,
    get_libs_dirs,
)
from tts_lua.constants import TTS_IDE_MSG_PROGRESS
from tts_lua.luabundler import bundle

log = logging.getLogger("ttsclient")


async def _command_progress(
    ide_com, iteration=0, total=100, prefix="", suffix="Prepare"
):
    if not ide_com:
        return
    await ide_com.send(
        {
            "messageID": TTS_IDE_MSG_PROGRESS,
            "iteration": iteration,
            "total": total,
            "prefix": prefix,
            "suffix": suffix,
        }
    )


async def fill_bundle_script_item(
    new_item, key, new_filepath, include_folders=None, bundle_cb=None
):
    data = await bundle(
        new_filepath, include_folders=include_folders, bundle_cb=bundle_cb
    )
    data = data.decode()
    new_item[key] = data


async def request_command_push(
    *_,
    export_dir: str = None,
    lib_dirs: list = None,
    ide_com: IDECommunication = None,
    **__,
):
    state_file = get_script_state_path(export_dir=export_dir)
    script_states = []
    lib_dirs = get_libs_dirs(lib_dirs)
    with open(state_file, "rb") as fp:
        old_script_states = json.loads(fp.read())

    keys_to_process = ("script", "ui")
    sending_progress = 30
    progress_len = len(old_script_states) * len(keys_to_process) + sending_progress
    current_progress_state = {"iteration": 1}

    async def progress_cb(success):
        await _command_progress(
            ide_com,
            iteration=current_progress_state["iteration"],
            total=progress_len,
            suffix=f"bundling",
        )
        current_progress_state["iteration"] += 1

    all_tasks = []
    for item in old_script_states:
        new_item = item.copy()
        for key in keys_to_process:
            new_filename = get_export_filename(item, key=key)
            new_filepath = os.path.join(export_dir, new_filename)
            if not os.path.exists(new_filepath):
                log.warning(
                    "File %s doesn't exists while present in last retrieved state",
                    new_filename,
                )
                continue

            if key == "script":
                all_tasks.append(
                    fill_bundle_script_item(
                        new_item,
                        key,
                        new_filepath=new_filepath,
                        include_folders=lib_dirs,
                        bundle_cb=progress_cb,
                    )
                )
            else:
                with open(new_filepath) as fp:
                    data = fp.read()
                await progress_cb(True)
                new_item[key] = data
        script_states.append(new_item)
    await asyncio.gather(*all_tasks)
    log.info("Requesting push")
    await _command_progress(
        ide_com,
        iteration=progress_len - sending_progress,
        total=progress_len,
        suffix=f" sending",
    )
    return {"messageID": 1, "scriptStates": script_states}


async def request_command_pull(*_, **__):
    return {"messageID": 0}


async def request_command_error(command=None, *_, **__):
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


async def connect_to_tts_server(host, port):
    print("Connecting to TTS server")
    t0 = time.time()
    reader, writer = await asyncio.open_connection(host=host, port=port)
    print("Connected to TTS server", time.time() - t0)
    return reader, writer


async def tts_query(command, host="127.0.0.1", port=39999, ide_port=39998, **kwargs):
    t0 = time.time()
    ide_com = IDECommunication(host=host, port=ide_port)
    await _command_progress(
        ide_com,
        iteration=0,
        total=100,
        prefix="Pushing files",
        suffix="Prepare",
    )

    connect_task = asyncio.create_task(connect_to_tts_server(host=host, port=port))

    request_func = REQUESTS_COMMANDS.get(
        command, partial(request_command_error, command=command)
    )
    export_dir = kwargs.get("export_dir")
    wait_file_path = None
    if command == "pull" and export_dir:
        wait_file_path = os.path.join(export_dir, RELOAD_FILE)
        os.remove(wait_file_path)

    message, (reader, writer) = await asyncio.gather(
        request_func(**kwargs, ide_com=ide_com), connect_task
    )
    json_msg = json.dumps(message).encode()
    writer.write(json_msg)
    await writer.drain()

    log.debug("Close the connection")
    writer.close()
    await writer.wait_closed()

    await _command_progress(
        ide_com,
        iteration=100,
        total=100,
        suffix=f"Complete",
    )

    if wait_file_path:
        await wait_for_file(wait_file_path)
    print("Took ", time.time() - t0)
