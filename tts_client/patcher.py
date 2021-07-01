import asyncio
import glob
import json
import os
import time

from tts_client.direct_ide import IDECommunication, command_progress
from tts_folder.export_dir import (
    get_hot_reload_path,
    HOT_RELOAD_TIMES,
    HOT_RELOAD_GUID_FILES,
    HOT_RELOAD_FILES_GUID,
)
from tts_lua.constants import TTS_MESSAGE_ID, TTS_MSG_EXEC_LUA
from tts_lua.luabundler import bundle

APPLY_CODE_LUA = """function __apply_code(guid, new_code)
    local obj = getObjectFromGUID(guid)
    if obj == nil then
        return "Not found " .. guid
    else
        obj.setLuaScript(new_code)
        obj.reload()
        return "Updated " .. guid
    end
end"""


async def request_patch_object(
    guid: str = None,
    file_path: str = None,
    export_dir: str = None,
    lib_dirs: list = None,
    do_return: bool = False,
    **_,
):

    if not file_path and "tags:" not in guid:
        search_pattern = os.path.join(export_dir, f"*-{guid}.ttslua")
        candidates = glob.glob(search_pattern)
        if candidates:
            file_path = candidates[0]
            print(file_path)
    if not file_path:
        raise ValueError("File path not found")

    updated_code = await _get_updated_code(file_path, lib_dirs=lib_dirs)
    snippet = f"""{APPLY_CODE_LUA}
return __apply_code("{guid}", [===[{updated_code}]===])
    """
    message = {
        TTS_MESSAGE_ID: TTS_MSG_EXEC_LUA,
        "guid": "-1",
        "script": snippet,
    }
    if do_return:
        message["returnID"] = int(time.time())
    return message


async def _get_updated_code(file_path, lib_dirs, bundle_cb=None):
    updated_code = await bundle(
        file_path, include_folders=lib_dirs, bundle_cb=bundle_cb
    )
    if updated_code is None:
        with open(file_path, "r", encoding="utf-8") as fp:
            updated_code = fp.read()
    else:
        updated_code = updated_code.decode()
    return updated_code


async def request_command_soft_push(
    *_,
    export_dir: str = None,
    lib_dirs: list = None,
    ide_com: IDECommunication = None,
    do_return=True,
    **__,
):
    hot_reload_state_path = get_hot_reload_path(export_dir=export_dir)
    if not os.path.exists(hot_reload_state_path):
        raise ValueError("Hot reload not initialized, cant be used")

    with open(hot_reload_state_path, "r", encoding="utf-8") as fp:
        hot_reload_state = json.load(fp)

    guid_to_update = set()
    new_time = time.time()

    for file_path, last_update in hot_reload_state.get(HOT_RELOAD_TIMES, {}).items():
        if os.path.getmtime(file_path) > last_update:
            guids = hot_reload_state.get(HOT_RELOAD_FILES_GUID, {}).get(file_path, [])
            guid_to_update.update(guids)
            hot_reload_state[HOT_RELOAD_TIMES][file_path] = new_time

    if "1" in guid_to_update:
        print("Can't update global in hot patch")
    guid_to_update.discard("1")
    tasks = []

    progress_len = len(guid_to_update)
    current_progress_state = {"iteration": 1}

    async def progress_cb(success):
        await command_progress(
            ide_com,
            iteration=current_progress_state["iteration"],
            total=progress_len,
            suffix=f"bundling",
        )
        current_progress_state["iteration"] += 1

    for idx, guid in enumerate(guid_to_update):
        for file_path in glob.glob(os.path.join(export_dir, f"*-{guid}.ttslua")):
            tasks.append(
                {
                    "guid": guid,
                    "coro": asyncio.create_task(
                        _get_updated_code(
                            file_path, lib_dirs=lib_dirs, bundle_cb=progress_cb
                        )
                    ),
                }
            )

    if not tasks:
        return {
            TTS_MESSAGE_ID: TTS_MSG_EXEC_LUA,
            "guid": "-1",
            "script": """print("Nothing to update")""",
        }

    results = await asyncio.gather(*[it["coro"] for it in tasks])

    new_codes = {it["guid"]: res for it, res in zip(tasks, results)}
    apply_codes = [
        f'__apply_code("{guid}", [===[{updated_code}]===])'
        for guid, updated_code in new_codes.items()
    ]
    apply_codes_str = "\n".join(apply_codes)
    snippet = f"""{APPLY_CODE_LUA}
    {apply_codes_str}
    return "Updated {",".join(new_codes.keys())}"
        """
    message = {
        TTS_MESSAGE_ID: TTS_MSG_EXEC_LUA,
        "guid": "-1",
        "script": snippet,
    }
    if do_return:
        message["returnID"] = int(time.time())
    with open(hot_reload_state_path, "w", encoding="utf-8") as fp:
        json.dump(hot_reload_state, fp)
    return message
