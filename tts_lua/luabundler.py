import asyncio
import os
import subprocess
import logging
import time

log = logging.getLogger(__name__)


def get_binary():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(
        base_dir,
        "../node_modules",
        "luabundler",
        "bin",
        "run.cmd" if os.name == "nt" else "run",
    )


async def run(cmd, collect_cb=None):
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=1024 * 1024 * 10
    )

    stdout, stderr = await proc.communicate()

    result = None
    success = False
    if proc.returncode != 0:
        error_msg = await proc.stderr.read()
        log.error(
            "Error running command %s code %s message %s",
            cmd,
            proc.returncode,
            error_msg.decode(),
        )
    else:
        success = True
        result = stdout
    if collect_cb:
        await collect_cb(success)
    return result


async def bundle(source_file, include_folders=None, bundle_cb=None):
    include_folders = include_folders or []
    command = [get_binary(), "bundle", source_file]
    log.debug("Bundle %s", source_file)
    for folder in include_folders:
        command.extend(
            [
                "-p",
                os.path.join(folder, "?.ttslua"),
                "-p",
                os.path.join(folder, "?.lua"),
            ]
        )
    bundle_res = await run(command, collect_cb=bundle_cb)
    log.debug("Done %s", source_file)
    return bundle_res


def get_unbundle_result(out, fallback=None):

    if out.returncode != 0:
        error_msg = out.stderr
        if "No metadata found" in error_msg:
            log.debug(error_msg)
        else:
            log.error(error_msg)
        return fallback
    else:
        return out.stdout.rstrip() + "\n"


def unbundle(data):
    command = [get_binary(), "unbundle"]
    out = subprocess.run(command, capture_output=True, input=data, encoding="utf-8")
    return get_unbundle_result(out, fallback=data)


def unbundle_file(filepath):
    command = [get_binary(), "unbundle", filepath]
    out = subprocess.run(command, capture_output=True, encoding="utf-8")

    return get_unbundle_result(out, fallback=None)
