import asyncio
import functools
import json
import logging
import os
import re
import time
from functools import partial

from tts_client.direct_ide import IDECommunication, command_progress
from tts_client.patcher import request_patch_object, request_command_soft_push
from tts_folder.export_dir import (
    get_script_state_path,
    get_export_filename,
    RELOAD_FILE,
    get_libs_dirs,
)
from tts_lua.constants import TTS_MSG_EXEC_LUA, TTS_MESSAGE_ID
from tts_lua.luabundler import bundle

log = logging.getLogger("ttsclient")


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
    with open(state_file, "rb") as fp:
        old_script_states = json.loads(fp.read())

    keys_to_process = ("script", "ui")
    sending_progress = 30
    progress_len = len(old_script_states) * len(keys_to_process) + sending_progress
    current_progress_state = {"iteration": 1}

    async def progress_cb(success):
        await command_progress(
            ide_com,
            iteration=current_progress_state["iteration"],
            total=progress_len,
            suffix=f"bundling",
        )
        current_progress_state["iteration"] += 1

    all_tasks = []
    for item in old_script_states:
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
                        item,
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
                item[key] = data
        script_states.append(item)
    await asyncio.gather(*all_tasks)
    log.info("Requesting push")
    await command_progress(
        ide_com,
        iteration=progress_len - sending_progress,
        total=progress_len,
        suffix=f" sending",
    )
    # Fill new script state in script state file
    with open(state_file, "w") as fp:
        json.dump(old_script_states, fp, indent=4)

    return {TTS_MESSAGE_ID: 1, "scriptStates": script_states}


async def request_command_pull(*_, **__):
    return {TTS_MESSAGE_ID: 0}


async def request_command_error(command=None, *_, **__):
    raise ValueError(f"Command {command} not recognized")


REQUESTS_COMMANDS = {
    "push": request_command_push,
    "pull": request_command_pull,
    "soft_push": request_command_soft_push,
}


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


async def _clean_close(writer):
    await writer.drain()
    writer.close()
    await writer.wait_closed()


def client_command(prefix=None, auto_complete=True):
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(
            *args, host="127.0.0.1", port=39999, ide_port=39998, lib_dirs=None, **kwargs
        ):
            # Some fancy foo stuff
            ide_com = IDECommunication(host=host, port=ide_port)
            await command_progress(
                ide_com,
                iteration=0,
                total=100,
                prefix=prefix,
                suffix="Prepare",
            )
            connect_task = asyncio.create_task(
                connect_to_tts_server(host=host, port=port)
            )

            res = await func(
                *args,
                connect_task=connect_task,
                ide_com=ide_com,
                lib_dirs=get_libs_dirs(lib_dirs),
                **kwargs,
            )
            if auto_complete:
                await command_progress(
                    ide_com,
                    iteration=100,
                    total=100,
                    prefix=prefix,
                    suffix="Complete",
                )

            return res

        return wrapped

    return wrapper


@client_command(prefix="Sync files", auto_complete=False)
async def tts_query(command, connect_task, ide_com, **kwargs):
    t0 = time.time()

    request_func = REQUESTS_COMMANDS.get(
        command, partial(request_command_error, command=command)
    )
    export_dir = kwargs.get("export_dir")
    wait_file_path = None
    if command == "pull" and export_dir:
        wait_file_path = os.path.join(export_dir, RELOAD_FILE)
        if os.path.exists(wait_file_path):
            os.remove(wait_file_path)

    message, (reader, writer) = await asyncio.gather(
        request_func(**kwargs, ide_com=ide_com), connect_task
    )
    writer.write(json.dumps(message).encode())
    await _clean_close(writer)

    await command_progress(
        ide_com,
        iteration=100,
        total=100,
        suffix=f"Complete",
    )

    if wait_file_path:
        await wait_for_file(wait_file_path)
    print("Took ", time.time() - t0)


@client_command(prefix="Running snippet")
async def tts_inject_snippet(
    file_path,
    connect_task,
    lib_dirs=None,
    **_,
):
    reader, writer = await connect_task
    on_guid = "-1"

    # Parse GUID
    with open(file_path, "r") as fp:
        file_text = fp.read()
    guid_match = re.match(r"^-- FOR_GUID : (.+)$", file_text, re.MULTILINE)
    if guid_match:
        print("Using guid ", guid_match.group(1))
        on_guid = guid_match.group(1)

    snippet = await bundle(file_path, include_folders=lib_dirs)
    snippet = file_text if snippet is None else snippet.decode()
    message = {
        TTS_MESSAGE_ID: TTS_MSG_EXEC_LUA,
        "guid": on_guid,
        "script": snippet,
        "returnID": int(time.time()),
    }
    writer.write(json.dumps(message).encode())
    await _clean_close(writer)


@client_command(prefix="Push object")
async def tts_push_object(
    file_path,
    object,
    connect_task,
    lib_dirs=None,
    export_dir=None,
    **_,
):
    reader, writer = await connect_task
    message = await request_patch_object(
        guid=object,
        file_path=file_path,
        lib_dirs=lib_dirs,
        export_dir=export_dir,
        do_return=True,
    )
    writer.write(json.dumps(message).encode())
    await _clean_close(writer)
