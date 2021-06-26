import os
import subprocess
import logging

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


def bundle(source_file, include_folders=None):
    include_folders = include_folders or []
    command = [get_binary(), "bundle", source_file]
    for folder in include_folders:
        command.extend(
            [
                "-p",
                os.path.join(folder, "?.ttslua"),
                "-p",
                os.path.join(folder, "?.lua"),
            ]
        )
    out = subprocess.run(command, capture_output=True)
    if out.returncode != 0:
        log.error(out.stderr)
    else:
        return out.stdout


def unbundle(data):
    command = [get_binary(), "unbundle"]
    out = subprocess.run(command, capture_output=True, input=data, encoding="utf-8")
    if out.returncode != 0:
        log.error(out.stderr)
        return data
    else:
        return out.stdout


def unbundle_file(filepath):
    command = [get_binary(), "unbundle", filepath]
    out = subprocess.run(command, capture_output=True)
    if out.returncode != 0:
        log.error(out.stderr)
        return data
    else:
        return out.stdout


if __name__ == "__main__":
    bundle(
        "/home/r3gis3r/Dev/tts_squad_tactics/miniature/Miniature.ttslua",
        include_folders=[
            os.path.join(os.path.expanduser("~"), "Documents", "Tabletop Simulator")
        ],
    )
