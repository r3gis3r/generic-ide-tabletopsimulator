import asyncio
import json
import logging

from tts_lua.constants import TTS_MESSAGE_ID, TTS_IDE_MSG_PROGRESS

log = logging.getLogger(__name__)


class IDECommunication(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    async def _start(self, timeout=2):
        log.debug("Connecting to the IDE server")
        fut = asyncio.open_connection(
                host=self._host, port=self._port
            )
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            log.info("Timeout, skipping communicate with IDE")
        except IOError:
            log.info("Unable to communicate with IDE")
        return None, None

    async def send(self, message):
        _, writer = await self._start()
        if writer:
            writer.write(json.dumps(message).encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()


async def command_progress(
    ide_com, iteration=0, total=100, prefix="", suffix="Prepare"
):
    if not ide_com:
        return
    await ide_com.send(
        {
            TTS_MESSAGE_ID: TTS_IDE_MSG_PROGRESS,
            "iteration": iteration,
            "total": total,
            "prefix": prefix,
            "suffix": suffix,
        }
    )