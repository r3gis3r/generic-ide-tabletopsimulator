import asyncio
import json
import logging

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